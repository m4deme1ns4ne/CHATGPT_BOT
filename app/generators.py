from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger
import httpx
import os

from logger import file_logger


@logger.catch
async def gpt(question: str):
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
    try:
        response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": str(question)}
                 ])

        return response.choices[0].message.content

    except Exception as err:
        logger.info(f"Ошибка при обработке запроса: {err}")
        raise Exception
