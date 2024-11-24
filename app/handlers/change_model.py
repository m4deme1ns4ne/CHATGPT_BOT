from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from loguru import logger

from app.logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.database.db import (
    DatabaseConfig, DatabaseConnection, UserManagement
)
from app.handlers.states import GPTState


router = Router()

file_logger()


@logger.catch
@router.message(F.text.in_(["Поменять нейросеть ↩️", "Выбрать нейросеть 🧠"]))
async def change_gpt_model(message: Message, state: FSMContext, bot: Bot):
    """
    Отправляет сообщение с кол-вом запросов

    Args:
        message (Message): Сообщение пользователя
        state (FSMContext): Состояние диалога
        bot (Bot): Бот
    """
    try:

        telegram_id = message.from_user.id

        config = DatabaseConfig()
        connection = DatabaseConnection(config)
        user_manager = UserManagement(connection)

        count_gpt_4o_mini = await user_manager.get_users_call_data(
                                                   telegram_id=telegram_id, 
                                                   model="gpt-4o-mini")
        count_gpt_4o = await user_manager.get_users_call_data(
                                                   telegram_id=telegram_id, 
                                                   model="gpt-4o")
        count_gpt_4o_mini_free = await user_manager.get_users_call_data(
                                                   telegram_id=telegram_id, 
                                                   model="gpt-4o-mini-free")
        count_gpt_o1 = await user_manager.get_users_call_data(
                                                   telegram_id=telegram_id, 
                                                   model="o1-preview")
        count_gpt_o1_mini = await user_manager.get_users_call_data(
                                                   telegram_id=telegram_id, 
                                                   model="o1-mini")

        await message.answer(f"""
Выберите нейросеть 🤖

Оставшиеся кол-во платных запросов:

*CHAT GPT 4o mini: {count_gpt_4o_mini[0]}*
*CHAT GPT 4o: {count_gpt_4o[0]}*

*CHAT GPT o1-mini: {count_gpt_o1_mini[0]}*
*CHAT GPT o1: {count_gpt_o1[0]}*

Оставшиеся кол-во бесплатных запросов:
*CHAT GPT 4o mini: {count_gpt_4o_mini_free[0]}*""",
            reply_markup=kb.main,
            parse_mode=ParseMode.MARKDOWN
        )

        await state.set_state(GPTState.selecting_model)  # Возвращаемся к выбору модели
    except Exception as err:
        logger.error(f"Ошибка при смене нейросети: {err}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
        return
