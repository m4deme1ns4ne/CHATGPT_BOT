import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from loguru import logger
import os

from logger import file_logger
from app.handlers import router


@logger.catch
async def main():

    load_dotenv()
    file_logger()

    global bot

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logger.info("Бот запущен")
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.error("Бот выключен")
