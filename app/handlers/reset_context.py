from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.database.db import (
    DatabaseConfig, DatabaseConnection, MessageHistory
)


router = Router()

file_logger()


@logger.catch
@router.message(F.text == "Сброс контекста 🔄")
async def reset_context(message: Message, state: FSMContext, bot: Bot):
    """ Сбрасывает контекст диалога

    Args:
        message (Message): Сообщение пользователя
        state (FSMContext): Состояние диалога
        bot (Bot): Бот
    """
    telegram_id = message.from_user.id
    try:
        config = DatabaseConfig()
        connection = DatabaseConnection(config)
        message_history = MessageHistory(connection) 
        # Очищаем контекст сообщений в базе данных
        await message_history.clear_message_history(telegram_id)
        await message.reply(cmd_message.reset_context_message)
    except Exception as err:
        logger.error(f"Ошибка при сбросе контекста: {err}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
        return
