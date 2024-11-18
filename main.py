import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from loguru import logger
import os

from app.logger import file_logger
from app.handlers import (change_model, static_messages, payments, 
                          process_generation, reset_context, select_model)


@logger.catch
async def main() -> None:

    load_dotenv()
    file_logger()

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    dp.include_routers(change_model.router, reset_context.router, 
                       static_messages.router, payments.router, 
                       select_model.router, process_generation.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logger.info("Бот запущен")
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.error("Бот выключен")
