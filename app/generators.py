from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger
import httpx
import os

from logger import file_logger

# Переменная для хранения истории сообщений
message_history = []

@logger.catch
async def gpt(question: str, model_gpt: str):
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
        logger.info(f"Ошибка при получении API_OPEN_AI: {err}")
        raise Exception

    # Добавляем новый вопрос в историю
    message_history.append({"role": "user", "content": str(question)})

    # Ограничиваем историю сообщений двумя последними
    if len(message_history) > 2:
        message_history = message_history[-2:]

    try:
        response = await client.chat.completions.create(
            model=model_gpt,
            messages=message_history
        )

        # Получаем ответ от GPT и добавляем его в историю
        gpt_response = response.choices[0].message.content
        message_history.append({"role": "assistant", "content": gpt_response})

        # Ограничиваем историю сообщений двумя последними
        if len(message_history) > 2:
            message_history = message_history[-2:]

        logger.info(f"Ответ GPT {model_gpt} получен")
        return gpt_response

    except Exception as err:
        logger.error(f"Ошибка при обработке запроса: {err}")
        raise Exception
