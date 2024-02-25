import requests
from googletrans import Translator
from transformers import AutoTokenizer


class GPT:
    def __init__(self):
        self.system_content = ("You are a polite AI assistant. You are a great specialist in footwear types."
                               "You know all the fashion footwear. You can answer any"
                               "question about trainers, boots and shoes. You must always give thorough details on "
                               "advantages and disadvantages if you are talking about footwear. You must analise all"
                               "the footwear and find the best one for the requests you receive. Always name the "
                               "brand and model of footwear if you are talking about it."
                               " Pay attention on the pricing if you are asked about a budget option.")
        self.URL = 'http://localhost:1234/v1/chat/completions'
        self.HEADERS = {"Content-Type": "application/json"}
        self.MAX_TOKENS_IN_QUEST = 2048
        self.TEMPERATURE = 0.9
        self.MAX_TOKENS_IN_ANS = 250

    def make_prompt(self, user_content, gpt_answer):
        translator = Translator()  # для лучшей работы использую переводчик
        t_user_content = translator.translate(f'{user_content}', src='ru', dest='en').text

        tokens_in_quest = self.count_tokens(t_user_content)  # подсчет токенов (запроса на английском языке)
        if tokens_in_quest > self.MAX_TOKENS_IN_QUEST:
            gpt_answer = ""
            return False, "Текст слишком большой! Пожалуйста, переформулируйте Ваш вопрос.", gpt_answer

        if user_content.lower() == "продолжи!":
            assistant_content = " " + gpt_answer  # вносим историю ответов нейросети
            task = " "

        else:
            task = t_user_content
            gpt_answer = ""
            assistant_content = " "

        resp = requests.post(
            # эндпоинт
            url=self.URL,
            # заголовок
            headers=self.HEADERS,
            # тело запроса
            json={
                "messages": [
                    {"role": "system", "content": self.system_content},
                    {"role": "user", "content": task},
                    {"role": "assistant", "content": assistant_content}
                ],
                "temperature": self.TEMPERATURE,
                "max_tokens": self.MAX_TOKENS_IN_ANS,
            }
        )

        # Печатаем ответ
        if resp.status_code == 200 and 'choices' in resp.json():
            result = resp.json()['choices'][0]['message']['content']

            if result == "":
                gpt_answer = ""
                return False,  ("Ответ окончен.\n\n"
                                "Жду Ваши вопросы!"), gpt_answer

            t_result = translator.translate(f'{result}', src='en', dest='ru').text
            gpt_answer += result
            return True, t_result, gpt_answer, result
        else:
            return False, ("Не удалось получить ответ от нейросети.\n"
                           f"Текст ошибки: {resp.json()}")

    @staticmethod
    def count_tokens(prompt):
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")  # название модели
        return len(tokenizer.encode(prompt))
