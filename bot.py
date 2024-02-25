# Бунин Николай, 21 группа
# модель: mistralai/Mistral-7B-Instruct-v0.2
# ----------------------------------------------------ИМПОРТЫ-----------------------------------------------------------
from dotenv import load_dotenv
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, BotCommand, BotCommandScope
from gpt import GPT
import json
import logging

load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token=token)

gpt = GPT()
# ------------------------------------------------------ЛОГИ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H",
    filename="log_file.txt",
    filemode="w",
)


@bot.message_handler(commands=['debug'])
def send_logs(message):
    user_id = message.chat.id

    if user_id == 922598615:
        try:

            with open("log_file.txt", "rb") as f:
                bot.send_document(message.chat.id, f)

        except telebot.apihelper.ApiTelegramException:

            bot.send_message(message.chat.id, "Логов пока нет.")

    else:
        bot.send_message(message.chat.id, "У Вас недостаточно прав для использования этой команды.")


# ------------------------------------------------------JSON------------------------------------------------------------
def save_to_json():
    with open('user_data.json', 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2)


def load_from_json():
    # noinspection PyBroadException
    try:
        with open('user_data.json', 'r+', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}

    return data


user_data = load_from_json()
# --------------------------------------------------КЛАВИАТУРЫ----------------------------------------------------------

main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Поболтаем!")
continue_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("Продолжи!", "Выход")
exit_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add("Выход")


# ----------------------------------------------------ЗАПУСК------------------------------------------------------------
@bot.message_handler(commands=["start"])
def start_bot(message):
    logging.info("Бот запущен")

    commands = [  # Установка списка команд с областью видимости и описанием
        BotCommand('start', 'перезапустить бота'),
        BotCommand('help', 'узнайте о доступных командах'),
        BotCommand('talk', 'начать диалог с нейросетью'),
        BotCommand('exit', 'завершить диалог с нейросетью')
    ]

    bot.set_my_commands(commands)
    BotCommandScope('private', chat_id=message.chat.id)

    load_from_json()  # создание пользователя
    user_id = str(message.from_user.id)
    user_data[user_id] = {"gpt_answer": "", "proccessing answer": False}
    save_to_json()

    #  приветствие
    bot.send_message(message.chat.id, 'Привет! Я бот с нейросетью под капотом. '
                                      'Я призван помогать Вам в вопросах подбора обуви на любой вкус,'
                                      ' так что, если таковые имеются, '
                                      'смело задавайте!\n\n'
                                      'Чтобы начать диалог с нейросетью, необходимо нажать на'
                                      ' кнопку "Поболтаем!" либо использовать команду /talk .',
                     reply_markup=main_menu_keyboard)


@bot.message_handler(commands=["help"])
def tell_about_bot(message):
    text = ("Привет! Тут Вы найдете основную информацию о моих функциях.\n\n"
            "/start - это как проснуться заново, забыв всю свою прошлую жизнь! Только для бота..\n\n"
            "/help - поможет Вам узнать основную информацию о моих функциях\n\n"
            '/talk или кнопка "Поболтаем!" - позволяет мне выступить посредником между Вами и нейросетью, а Вам - '
            'получить от нее ответ на Ваш вопрос.\n\n'
            'После того, как нейросеть ответит на Ваш вопрос, Вы сможете попросить ее продолжить свой ответ, нажав на'
            ' кнопку "Продолжи!"\n\n'
            '/exit или кнопка "Выход" - позволит Вам закончить диалог с нейросетью.')

    bot.reply_to(message, text=text)

    logging.info("сообщение с инструкцией по использованию бота успешно отправлено")


# -----------------------------------------------РАБОТА С GPT-----------------------------------------------------------
@bot.message_handler(content_types=['text'], func=lambda message: message.text.lower() == "поболтаем!")
@bot.message_handler(commands=['talk'])
def take_issue(message):
    user_id = str(message.from_user.id)

    if user_data[user_id]["proccessing answer"]:  # нельзя задать еще один вопрос, когда нейросеть уже генерирует другой
        logging.debug("попытка задать еще один вопрос, когда нейросеть уже генерирует другой")

        bot.reply_to(message, "Нейросеть уже отвечает на Ваш вопрос. Прежде чем задать следующий,"
                              " дождитесь ответа на предыдущий.")
        return

    bot.send_message(message.chat.id, 'Можете задать Ваш вопрос.\n\n'
                                      'Важно:\n\n'
                                      "0. Нейросеть призвана предоставить вам информацию именно об обуви, поэтому"
                                      " будьте готовы, что, задав вопрос на любую тему, получите ответ так или иначе, "
                                      "связанный с обувью.\n\n"
                                      '1. Запрос должен быть текстовым,'
                                      ' иначе у Вас просто не получится его сделать.\n\n'
                                      '2. Если захотите продолжить, то'
                                      ' смело жмите на кнопку "Продолжи!", '
                                      'которая появится после Вашего первого запроса.\n\n'
                                      '3. Если хотите воспользоваться командами, то Вам нужно сначала '
                                      'завершить диалог с нейросетью. Иначе команда будет воспринята как запрос.',
                     reply_markup=exit_keyboard)

    logging.info("сообщение с инструкцией по созданию промпта успешно отправлено")

    bot.register_next_step_handler(message, ask_gpt)


def ask_gpt(message):
    user_id = str(message.from_user.id)

    prompt = message.text

    if not prompt:  # проверка типа сообщения
        logging.error("неправильный формат запроса")

        bot.send_message(message.chat.id, "Кажется, Вы отправили не текстовый запрос. Я пока не умею принимать"
                                          " такие. Попробуйте отправить что-то другое!")

        bot.register_next_step_handler(message, ask_gpt)

        return

    if prompt.lower() == "продолжи!":
        if user_data[user_id]["gpt_answer"] == "":

            logging.error("попытка продолжить, когда вопрос еще не была задан")

            bot.reply_to(message, "Так как запроса еще не было, то и продолжать пока нечего. Чтобы "
                                  "воспользоваться данной опцией, сначала задайте ваш вопрос.")
            bot.register_next_step_handler(message, ask_gpt)
            return

    if prompt in ["Выход", "/exit"]:
        bot.send_message(message.chat.id, "До скорого!", reply_markup=main_menu_keyboard)
        user_data[user_id]["gpt_answer"] = ""
        save_to_json()

        logging.info("выход осуществлен успешно")
        return

    user_data[user_id]["proccessing answer"] = True

    bot.send_chat_action(message.chat.id, "TYPING")
    answer_gpt = gpt.make_prompt(user_content=prompt, gpt_answer=user_data[user_id]["gpt_answer"])

    user_data[user_id]["proccessing answer"] = False
    user_data[user_id]["gpt_answer"] = answer_gpt[2]  # сохраняем ответ нейросети (если он есть)
    save_to_json()

    if not answer_gpt[0]:  # если ответ окончен или произошла ошибка

        if answer_gpt[1] == "Ответ окончен.\n\nЖду Ваших вопросов!":

            logging.info("ответ нейросети окончен")

        else:

            logging.error(f"Произошла ошибка: {answer_gpt[1]}")

        bot.send_message(message.chat.id, answer_gpt[1], reply_markup=exit_keyboard)

    else:  # если запрос успешно пришел
        bot.reply_to(message, answer_gpt[1], reply_markup=continue_keyboard)

        logging.info("Ответ нейросети успешно отправлен")

    bot.register_next_step_handler(message, ask_gpt)


# -----------------------------------------ОТВЕТ НА ОСТАЛЬНОЕ-----------------------------------------------------------
CONTENT_TYPES = ["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice"]


@bot.message_handler(content_types=CONTENT_TYPES)
def any_msg(message):
    user_id = str(message.from_user.id)

    if user_data[user_id]["proccessing answer"]:

        logging.debug("попытка задать еще один вопрос, когда нейросеть уже генерирует другой")

        bot.reply_to(message, "Нейросеть уже отвечает на Ваш вопрос. Прежде чем задать следующий,"
                              " дождитесь ответа на предыдущий.")

    else:

        logging.debug("попытка общения с ботом")

        bot.send_message(message.chat.id, 'Отлично сказано! Если хотите задать вопрос, то сначала нажмите на кнопку'
                                          ' "Поболтаем!"', reply_markup=main_menu_keyboard)


bot.infinity_polling()  # запуск бота
