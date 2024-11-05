from loguru import logger
from app.logger import file_logger
from openai import AsyncOpenAI
import httpx
import os

from app.database.db import DATABASE
from app.cmd_message import promt


file_logger()


class GPTResponse:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPEN_AI_TOKEN")
        self.proxies = os.getenv("PROXY")
        self.local_address = "0.0.0.0"
        self.db = DATABASE()

    async def get_openai_client(self):
        """
        Создание клиента OpenAI.
        """
        return AsyncOpenAI(
            api_key=self.api_key,
            http_client=httpx.AsyncClient(
                proxies=self.proxies,
                transport=httpx.HTTPTransport(local_address=self.proxies)
            )
        )

    @logger.catch
    async def gpt_answer(self, question: str, model_gpt: str, telegram_id: int) -> str:
        """
        Отправляет вопрос модели GPT и обрабатывает ответ.

        :param question (str): Строка с вопросом или запросом пользователя.
        :param model_gpt (str): Строка, обозначающая используемую модель GPT.
        :param telegram_id (int): Целочисленный идентификатор пользователя в Telegram.

        :return: Ответ от модели GPT в виде строки.
        """
        try:

            # Проверяем, существует ли пользователь, если нет — добавляем
            if not await self.db.user_exists(telegram_id):
                await self.db.add_user(telegram_id)
                logger.info(f"Добавлен новый пользователь с telegram_id: {telegram_id}")

            # Получаем историю сообщений для пользователя
            message_history = await self.db.get_message_history(telegram_id)

            # Добавляем новый вопрос в историю
            message_history.append({"role": "user", "content": str(question)})

            # Ограничиваем историю двумя последними сообщениями
            if len(message_history) > 6:
                message_history = message_history[-6:]

            # Создаем клиент OpenAI
            client = await self.get_openai_client()

            # Отправляем запрос в GPT
            response = await client.chat.completions.create(
                model=model_gpt,
                messages=[
                    {"role": "system", "content": str(promt)},
                    {"role": "user", "content": str(message_history)}
                ],
                max_tokens=1000,
                temperature=0.7,
                top_p=0.85,
                n=1,
                presence_penalty=0.5,
                frequency_penalty=0.5
            )

            # Получаем ответ от GPT
            gpt_response = response.choices[0].message.content
            message_history.append({"role": "assistant", "content": gpt_response})

            # Ограничиваем историю шестью последними сообщениями
            if len(message_history) > 6:
                message_history = message_history[-6:]

            # Сохраняем новые сообщения в базу данных и удаляем старые
            await self.db.save_message_history(telegram_id, message_history[-2:])

            logger.info(f"Ответ GPT {model_gpt} получен для пользователя {telegram_id}")
            return gpt_response

        except Exception as err:
            logger.error(f"Ошибка при обработке запроса для пользователя {telegram_id}: {err}")
            raise Exception("Произошла ошибка при обработке запроса.")
