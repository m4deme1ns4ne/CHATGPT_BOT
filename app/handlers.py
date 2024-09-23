from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger
from datetime import datetime, timedelta

from app.generators import gpt
from logger import file_logger
from . import cmd_message
from .count_token import count_tokens
import app.keyboards as kb

router = Router()

class Generate(StatesGroup):
    text_input = State()  # Состояние ожидания текста от пользователя
    text = State()        # Дополнительное состояние для генерации текста


@logger.catch
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    file_logger()
    try:
        await message.answer(cmd_message.start, reply_markup=kb.main)
        await state.clear()  # Очистка состояния при старте
    except Exception as err:
        logger.error(f"Ошибка при вводе команды /start: {err}")
        await message.answer(cmd_message.error)


@logger.catch
@router.message(F.text == "Поменять модель gpt")
async def change_gpt_model(message: Message, state: FSMContext):
    file_logger()
    try:
        # Возвращаем пользователя к выбору модели
        await message.answer("Выберите новую модель gpt:", reply_markup=kb.main)
        await state.clear()  # Очистка состояния, возвращаемся к выбору модели
    except Exception as err:
        logger.error(f"Ошибка при смене модели gpt: {err}")
        await message.answer(cmd_message.error)


@logger.catch
@router.message(F.text.in_(["Модель 4-o", "Модель 4-o-mini"]))
async def generate_gpt(message: Message, state: FSMContext):
    file_logger()

    # Проверяем, какое сообщение отправил пользователь
    if message.text == "Модель 4-o":
        model = "gpt-4o"
    elif message.text == "Модель 4-o-mini":
        model = "gpt-4o-mini"
    
    # Сохраняем выбранную модель в контексте FSM
    await state.update_data(model=model)

    # Запрос текста у пользователя
    await message.answer(f"Вы выбрали {model}. Введите текст для генерации:", reply_markup=kb.change_model)
    # Устанавливаем состояние ожидания текста
    await state.set_state(Generate.text_input)


@router.message(Generate.text_input)
async def process_generation(message: Message, state: FSMContext):

    telegram_id = message.from_user.id

    file_logger()

    # Получаем данные о модели из контекста
    data = await state.get_data()
    model = data.get("model")
    
    # Получение текста сообщения от пользователя
    user_input = message.text
    await state.set_state(Generate.text)
    
    # Отправка сообщения об ожидании
    await message.reply(f"✨ Модель: {model}. Среднее время ожидания: всего 5-19 секунд! ⏱🚀\nПожалуйста, подождите✨")

    try:
        # Генерация ответа на основе текста пользователя
        response = await gpt(user_input, model)
    except Exception as err:
        logger.error(f"Ошибка при генерации ответа gpt: {err}")
        await message.answer(cmd_message.error)
        return

    try:
        # Отправка сгенерированного ответа пользователю
        await message.edit_text(
            f"Ваш ответ, полученный с помощью {model}:\n\n{response}\n\nКол-во токенов: {count_tokens(user_input + response)}", 
            parse_mode="Markdown",
            reply_markup=kb.change_model  # Кнопка для смены модели
        )
        logger.info("Ответ gpt получен")
    except Exception as err:
        logger.error(f"Ошибка при отправке сообщения: {err}")
        await message.reply(cmd_message.error)
    await state.clear()


@router.message(Generate.text)
async def generate_error(message: Message):
    await message.answer("Подождите, ваше сообщение генерируется...")


@router.message(F.text)
async def error_select_model(message: Message):
    await message.answer("Выберите модель gpt", reply_markup=kb.main)
