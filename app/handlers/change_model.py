from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from loguru import logger

from logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.database.db import DATABASE


router = Router()

file_logger()


class Generate(StatesGroup):
    selecting_model = State()           # Состояние выбора модели
    text_input = State()                # Состояние ожидания текста от пользователя
    waiting_for_response = State()      # Ожидание ответа gpt



@logger.catch
@router.message(F.text.in_(["Поменять нейросеть ↩️", "Выбрать нейросеть 🧠"]))
async def change_gpt_model(message: Message, state: FSMContext, bot: Bot):
    """Отправляет сообщение с кол-вом запросов

    Args:
        message (Message): Сообщение пользователя
        state (FSMContext): Состояние диалога
        bot (Bot): Бот
    """
    try:

        telegram_id = message.from_user.id
        db = DATABASE()

        count_gpt_4o_mini = await db.get_users_call_data(telegram_id=telegram_id, 
                                                   model="gpt-4o-mini")
        count_gpt_4o = await db.get_users_call_data(telegram_id=telegram_id, 
                                              model="gpt-4o")

        await message.answer(f"Выберите нейросеть 🤖\n\nОставшиеся кол-во запросов:\n\n*CHAT GPT 4o mini: {count_gpt_4o_mini[0]}*\n\n*CHAT GPT 4o: {count_gpt_4o[0]}*", 
                             reply_markup=kb.main,
                             parse_mode=ParseMode.MARKDOWN)
        await state.set_state(Generate.selecting_model)  # Возвращаемся к выбору модели
    except Exception as err:
        logger.error(f"Ошибка при смене нейросети: {err}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
        return