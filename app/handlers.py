from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger
import time

from app.generators import gpt
from logger import file_logger
from app import cmd_message
from app.count_token import count_tokens
import app.keyboards as kb
from app.split_text import split_text
from .database.db import clear_message_history
from app.call_count_gpt import count_calls


router = Router()

# Переменная для хранения времени последнего сообщения
last_message_time = {}


class Generate(StatesGroup):
    selecting_model = State()           # Состояние выбора модели
    text_input = State()                # Состояние ожидания текста от пользователя
    waiting_for_response = State()      # Ожидание ответа gpt


@logger.catch
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):

    file_logger()

    try:
        await message.answer(cmd_message.start_message, reply_markup=kb.main)
        await state.clear()  # Очистка состояния при старте
        await state.set_state(Generate.selecting_model)  # Устанавливаем состояние выбора модели
    except Exception as err:
        logger.error(f"Ошибка при вводе команды /start: {err}")
        await message.answer(cmd_message.error_message)


@logger.catch
@router.message(F.text == "Поменять модель gpt")
async def change_gpt_model(message: Message, state: FSMContext):
    file_logger()
    try:
        await message.answer("Выберите новую модель gpt:", reply_markup=kb.main)
        await state.set_state(Generate.selecting_model)  # Возвращаемся к выбору модели
    except Exception as err:
        logger.error(f"Ошибка при смене модели gpt: {err}")
        await message.answer(cmd_message.error_message)


@logger.catch
@router.message(F.text == "Сброс контекста")
async def reset_context(message: Message, state: FSMContext):
    file_logger()
    telegram_id = message.from_user.id
    try:
        # Очищаем контекст сообщений в базе данных
        await clear_message_history(telegram_id)
        await message.reply(cmd_message.reset_context_message)
    except Exception as err:
        logger.error(f"Ошибка при сбросе контекста: {err}")
        await message.answer(cmd_message.error_message)


@logger.catch
@router.message(F.text == "❌Модель 4-o❌")
async def non_gpt_4o(message: Message, state: FSMContext):
    file_logger()
    await message.reply(f"Модель gpt-4o в режиме альфа тестирования недоступна, доступна только модель gpt-4o-mini")
    return


@logger.catch
@router.message(F.text.in_(["❌Модель 4-o❌", "✅Модель 4-o-mini✅"]))
async def select_model(message: Message, state: FSMContext):
    file_logger()
    model_mapping = {
        "❌Модель 4-o❌": "gpt-4o",
        "✅Модель 4-o-mini✅": "gpt-4o-mini"
    }
    model = model_mapping.get(message.text)
    
    await state.update_data(model=model)
    await state.set_state(Generate.text_input)

    await message.answer(f"Вы выбрали {model}. Введите текст для генерации:", reply_markup=await kb.change_model(model))


@logger.catch
@router.message(Generate.text_input)
@count_calls()
async def process_generation(message: Message, state: FSMContext):
    file_logger()

    telegram_id = message.from_user.id
    current_time = time.time()
    
    # Проверяем время последнего сообщения
    if telegram_id in last_message_time and current_time - last_message_time[telegram_id] < 1:
        # Если интервал между сообщениями меньше 0.5 секунд, не обрабатываем
        return

    last_message_time[telegram_id] = current_time

    # # Проверка подписки пользователя
    # if telegram_id not in [2050793273, 857805093]:
    #     await message.answer("Извините, вам отказано в доступе, скоро бот выйдет в общее пользование!")
    #     return

    data = await state.get_data()
    model = data.get("model")
    user_input = message.text

    # Проверяем длину сообщения
    if len(user_input) >= 4096:
        await message.answer("Сообщение слишком длинное. Пожалуйста, сократите его длину до 4096 символов.")
        # Возвращаем в состояние ожидания ввода текста
        await state.set_state(Generate.text_input)
        return

    # Проверяем текущее состояние
    current_state = await state.get_state()

    if current_state == Generate.waiting_for_response.state:
        await message.reply("Пожалуйста, дождитесь завершения обработки предыдущего запроса.")
        return

    # Устанавливаем состояние ожидания
    await state.set_state(Generate.waiting_for_response)

    await message.reply(f"✨ Модель: {model}. Среднее время ожидания: всего 5-19 секунд! ⏱🚀\nПожалуйста, подождите✨")

    try:
        response = await gpt(user_input, model, telegram_id)
    except Exception as err:
        logger.error(f"Ошибка при генерации ответа gpt: {err}")
        await message.answer(cmd_message.error_message)
        # Возвращаем в состояние ожидания ввода текста
        await state.set_state(Generate.text_input)
        return

    try:
        # Разделяем ответ на части по 4096 символов
        response_parts = split_text(response)
        for part in response_parts:
            await message.reply(
                f"Ваш ответ, полученный с помощью {model}:\n\n{part}\n\nКол-во токенов на input: {count_tokens(user_input)}\nКол-во токенов на output: {count_tokens(part)}", 
                parse_mode="Markdown",
                reply_markup=await kb.change_model(model)  # Кнопка для смены модели
            )
        logger.info("Ответ gpt получен и отправлен пользователю")
        
        # Возвращаем в состояние ожидания ввода текста
        await state.set_state(Generate.text_input)
    except Exception as err:
        logger.error(f"Ошибка при отправке сообщения: {err}")
        await message.reply(cmd_message.error_message)
        # Возвращаем в состояние ожидания ввода текста
        await state.set_state(Generate.text_input)
        return


@logger.catch
@router.message(F.text)
async def error_handling(message: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == Generate.waiting_for_response.state:
        await message.reply("Пожалуйста, дождитесь завершения обработки предыдущего запроса.")
    elif current_state == Generate.text_input.state:
        await process_generation(message, state)
    else:
        await message.answer("Выберите модель gpt", reply_markup=kb.main)
