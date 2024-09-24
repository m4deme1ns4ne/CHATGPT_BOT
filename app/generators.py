from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger
import httpx
import os
from logger import file_logger

@logger.catch
async def gpt(question: str, model_gpt: str):

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
    
    message_history = []
    
    # Добавляем новый вопрос в список сообщений
    message_history.append({"role": "user", "content": question})

    # Ограничиваем историю сообщений тремя последними
    if len(message_history) > 3:
        message_history.pop(0)

    try:
        response = await client.chat.completions.create(
            model=model_gpt,
            messages=message_history
        )

        # Получаем ответ от GPT и добавляем его в список сообщений
        gpt_response = response.choices[0].message.content
        message_history.append({"role": "assistant", "content": gpt_response})

        # Ограничиваем историю сообщений тремя последними
        if len(message_history) > 3:
            message_history.pop(0)

        logger.info(f"Ответ GPT {model_gpt} получен")

        print(message_history)

        return gpt_response

    except Exception as err:
        logger.error(f"Ошибка при обработке запроса: {err}")
        raise Exception
