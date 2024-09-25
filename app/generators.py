from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger
import httpx
import os

from logger import file_logger

# Переменная для хранения истории сообщений, используя telegram_id в качестве ключа
message_history = {}

@logger.catch
async def gpt(question: str, model_gpt: str, telegram_id: int) -> str:
    global message_history
    load_dotenv()
    file_logger()

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

    # Инициализируем историю сообщений для telegram_id, если её ещё нет
    if telegram_id not in message_history:
        message_history[telegram_id] = []

    # Добавляем новый вопрос в историю
    message_history[telegram_id].append({"role": "user", "content": str(question)})

    # Ограничиваем историю сообщений двумя последними
    if len(message_history[telegram_id]) > 2:
        message_history[telegram_id] = message_history[telegram_id][-2:]

    try:
        response = await client.chat.completions.create(
            model=model_gpt,
            messages=message_history[telegram_id]
        )

        # Получаем ответ от GPT и добавляем его в историю
        gpt_response = response.choices[0].message.content
        message_history[telegram_id].append({"role": "assistant", "content": gpt_response})

        # Ограничиваем историю сообщений двумя последними
        if len(message_history[telegram_id]) > 2:
            message_history[telegram_id] = message_history[telegram_id][-2:]

        logger.info(f"Ответ GPT {model_gpt} получен для пользователя {telegram_id}")
        return gpt_response

    except Exception as err:
        logger.error(f"Ошибка при обработке запроса для пользователя {telegram_id}: {err}")
        raise Exception
