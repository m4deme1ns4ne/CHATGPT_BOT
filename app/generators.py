from loguru import logger
from logger import file_logger
from openai import AsyncOpenAI
import httpx
import os

import app.database.db as db
from app.cmd_message import promt


file_logger()


async def get_openai_client():
    """Создание клиента OpenAI."""
    return AsyncOpenAI(
        api_key=os.getenv("OPEN_AI_TOKEN"),
        http_client=httpx.AsyncClient(
            proxies=os.getenv("PROXY"),
            transport=httpx.HTTPTransport(local_address="0.0.0.0")
        )
    )


@logger.catch
async def gpt(question: str, model_gpt: str, telegram_id: int) -> str:
    try:
        # Проверяем, существует ли пользователь, если нет — добавляем
        if not await db.users_exists(telegram_id):
            await db.add_users(telegram_id)
            logger.info(f"Добавлен новый пользователь с telegram_id: {telegram_id}")

        # Получаем историю сообщений для пользователя
        message_history = await db.get_message_history(telegram_id)

        # Добавляем новый вопрос в историю
        message_history.append({"role": "user", "content": str(question)})

        # Ограничиваем историю двумя последними сообщениями
        if len(message_history) > 6:
            message_history = message_history[-6:]

        # Создаем клиент OpenAI
        client = await get_openai_client()

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
        await db.save_message_history(telegram_id, message_history[-2:])

        logger.info(f"Ответ GPT {model_gpt} получен для пользователя {telegram_id}")
        return gpt_response

    except Exception as err:
        logger.error(f"Ошибка при обработке запроса для пользователя {telegram_id}: {err}")
        raise Exception("Произошла ошибка при обработке запроса.")
