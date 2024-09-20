from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.generators import gpt
from logger import file_logger
from . import cmd_message
from .count_token import count_tokens

router = Router()

class Generate(StatesGroup):
    text = State()

@logger.catch
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    file_logger()
    try:
        await message.answer("Добро пожаловать в телеграмм бота!")
        await state.clear()
    except Exception as err:
        logger.error(f"Ошибка при вводе команды /start: {err}")
        await message.answer(cmd_message.error)

@logger.catch
@router.message(F.text)
async def generate(message: Message, state: FSMContext):
    file_logger()

    # Отправка начального сообщения
    response_message = await message.reply("✨ Среднее время ожидания: всего 5-19 секунд! ⏱🚀\nПожалуйста, подождите✨")
    await state.set_state(Generate.text)
    try:
        # Генерация ответа
        response = await gpt(message.text)
    except Exception as err:
        logger.error(f"Ошибка при генерации ответа gpt: {err}")
        await message.answer(cmd_message.error)
    try:
        # Обновление сообщения
        await response_message.edit_text(
            f"Ваш ответ полученный с помощью модели gpt-4-o:\n\n{response}\n\nКол-во токенов: {count_tokens(message.text+response)}", parse_mode="Markdown"
            )
        logger.info("Ответ gpt получен")
    except Exception as err:
        logger.error(f"Ошибка при обновлении сообщения: {err}")
        await message.reply(cmd_message.error)
    await state.clear()

@router.message(Generate.text)
async def generate_error(message: Message):
    await message.answer("Подождите, ваше сообщение генерируется...")
