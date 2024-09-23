from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger
import httpx
import os
from logger import file_logger

from .database import init_db, add_message_to_db, get_last_three_messages, clean_old_messages


@logger.catch
async def gpt(question: str, model_gpt: str):

    load_dotenv()
    file_logger()

    init_db()  # Инициализация базы данных

    try:
        client = AsyncOpenAI(api_key=os.getenv("OPEN_AI_TOKEN"),
                             http_client=httpx.AsyncClient(
                                 proxies=os.getenv("PROXY"),
                                 transport=httpx.HTTPTransport(local_address="0.0.0.0")
                             ))
        logger.info("API_OPEN_AI обработан")
    except Exception as err:
        logger.error(f"Ошибка при получении API_OPEN_AI: {err}")
        raise Exception

    # Добавляем новый вопрос в базу данных
    add_message_to_db("user", question)

    # Ограничиваем историю сообщений тремя последними
    clean_old_messages()

    message_history = get_last_three_messages()

    try:
        response = await client.chat.completions.create(
            model=model_gpt,
            messages=message_history
        )

        # Получаем ответ от GPT и добавляем его в базу данных
        gpt_response = response.choices[0].message.content
        add_message_to_db("assistant", gpt_response)

        # Ограничиваем историю сообщений тремя последними
        clean_old_messages()

        logger.info(f"Ответ GPT {model_gpt} получен")
        return gpt_response

    except Exception as err:
        logger.error(f"Ошибка при обработке запроса: {err}")
        raise Exception
