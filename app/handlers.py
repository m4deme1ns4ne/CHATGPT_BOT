from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from loguru import logger

from app.generators import gpt
from logger import file_logger
from app import cmd_message
from app.count_token import count_tokens
import app.keyboards as kb
from app.split_text import split_text
from .database.db import clear_message_history
from app.call_count_gpt import count_calls
from .database.redis import check_time_spacing_between_messages, del_redis_id
from .calculate_message_length import calculate_message_length
from .escape_markdown import escape_markdown


router = Router()

file_logger()


class Generate(StatesGroup):
    selecting_model = State()           # Состояние выбора модели
    text_input = State()                # Состояние ожидания текста от пользователя
    waiting_for_response = State()      # Ожидание ответа gpt


@logger.catch
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    try:
        await message.answer(cmd_message.start_message, reply_markup=kb.main)
        await state.clear()  # Очистка состояния при старте
        await state.set_state(Generate.selecting_model)  # Устанавливаем состояние выбора модели
    except Exception as err:
        logger.error(f"Ошибка при вводе команды /start: {err}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )


@logger.catch
@router.message(F.text == "Поменять модель gpt 🤖")
async def change_gpt_model(message: Message, state: FSMContext, bot: Bot):
    try:
        await message.answer("Выберите новую модель gpt:", reply_markup=kb.main)
        await state.set_state(Generate.selecting_model)  # Возвращаемся к выбору модели
    except Exception as err:
        logger.error(f"Ошибка при смене модели gpt: {err}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )


@logger.catch
@router.message(F.text == "Сброс контекста 🔄")
async def reset_context(message: Message, state: FSMContext, bot: Bot):
    telegram_id = message.from_user.id
    try:
        # Очищаем контекст сообщений в базе данных
        await clear_message_history(telegram_id)
        await message.reply(cmd_message.reset_context_message)
    except Exception as err:
        logger.error(f"Ошибка при сбросе контекста: {err}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )


@logger.catch
@router.message(F.text.in_(["❌Модель 4-o❌", "✅Модель 4-o-mini✅"]))
async def select_model(message: Message, state: FSMContext):
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
async def process_generation(message: Message, state: FSMContext, bot: Bot):

    await bot.send_chat_action(message.chat.id, "typing")

    telegram_id = message.from_user.id
    
    # Проверяем время последнего сообщения
    if not await check_time_spacing_between_messages(telegram_id):
        # Если интервал между сообщениями меньше 0.5 секунд, не обрабатываем
        return

    data = await state.get_data()
    model = data.get("model")
    user_input = message.text

    if model == "gpt-4o" and telegram_id != 857805093:
        await message.reply(f"Модель gpt-4o в режиме альфа тестирования недоступна, доступна только модель gpt-4o-mini")
        return
    
    lenght_message_user = calculate_message_length(user_input)

    if lenght_message_user >= 4096:
        await message.answer(f"Сообщение слишком длинное. Пожалуйста, сократите его длину до 4096 символов.\n\nДлина отправленного сообщения: {lenght_message_user}")
        await state.set_state(Generate.text_input)
        return

    current_state = await state.get_state()

    if current_state == Generate.waiting_for_response.state:
        await message.reply("Пожалуйста, дождитесь завершения обработки предыдущего запроса.")
        return

    await state.set_state(Generate.waiting_for_response)

    # Отправляем сообщение с ожиданием и сохраняем его ID
    waiting_message = await message.reply(f"✨ Модель: {model}.\nСреднее время ожидания: всего 5-19 секунд! ⏱🚀\nПожалуйста, подождите✨")

    try:
        await bot.send_chat_action(message.chat.id, "typing")
        text_from_gpt = await gpt(user_input, model, telegram_id)
        response = escape_markdown(text_from_gpt)
    except Exception as err:
        logger.error(f"Ошибка при генерации ответа gpt: {err}")
        await bot.edit_message_text(
            chat_id=waiting_message.chat.id,
            message_id=waiting_message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
        await state.set_state(Generate.text_input)
        return

    try:
        response_parts = split_text(response)

        # Инициализация индекса
        total_parts, index = len(response_parts), 0

        # Цикл while для обработки всех частей списка
        while index < total_parts:
            part = response_parts[index]

            if index == 0:
                # Отправляем первое сообщение – обновляем старое
                await bot.edit_message_text(
                    chat_id=waiting_message.chat.id,
                    message_id=waiting_message.message_id,
                    text=part,
                    reply_markup=kb.report_an_error,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # Отправляем новое сообщение для каждой последующей части
                await message.reply(part,
                                    reply_markup=kb.report_an_error,
                                    parse_mode=ParseMode.MARKDOWN_V2
                                    )

            # Отправляем информацию о модели, если telegram_id соответствует
            if telegram_id == 857805093:
                await message.answer(
                    f"Model: {model}\nNumber of tokens per input: {count_tokens(user_input)}\nNumber of tokens per output: {count_tokens(part)}",
                    )

            # Увеличиваем индекс для перехода к следующей части
            index += 1
        
        logger.info(f"Ответ gpt получен и отправлен пользователю: {telegram_id}")
        await state.set_state(Generate.text_input)
        await del_redis_id(telegram_id)
    except Exception as err:
        logger.error(f"Ошибка при отправке сообщения: {err}")
        await bot.edit_message_text(
            chat_id=waiting_message.chat.id,
            message_id=waiting_message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
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
