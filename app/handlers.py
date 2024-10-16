from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from loguru import logger
from pydub import AudioSegment
import os

import app.keyboards as kb
import app.database.redis as rd
from app.generators import gpt
from logger import file_logger
from app import cmd_message
from app.count_token import count_tokens
from app.split_text import split_text
from app.database.db import clear_message_history
from app.call_count_gpt import count_calls
from app.calculate_message_length import calculate_message_length
from app.transcribe_audio import transcribe_audio
from app.correct_text import correct_text
from aiogram.utils.text_decorations import markdown_decoration


router = Router()

file_logger()


class Generate(StatesGroup):
    selecting_model = State()           # Состояние выбора модели
    text_input = State()                # Состояние ожидания текста от пользователя
    waiting_for_response = State()      # Ожидание ответа gpt


@logger.catch
@router.message(F.text.in_(["Вернуться в главное меню ↩️", "/start", "Назад ↩️"]))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    try:
        await message.answer(cmd_message.start_message, reply_markup=kb.most_high_main)
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
@router.message(F.text == "Подписка 🌟")
async def command_pay(message: Message, state: FSMContext, bot: Bot):
    await message.reply("Здесь будет информация про подписку...", reply_markup=kb.back)


@logger.catch
@router.message(F.text == "F.A.Q ❓")
async def comman_faq(message: Message, state: FSMContext, bot: Bot):
    await message.reply(cmd_message.faq,
                        parse_mode=ParseMode.MARKDOWN)


@logger.catch
@router.message(F.text.in_(["Поменять нейросеть ↩️", "Выбрать нейросеть 🧠"]))
async def change_gpt_model(message: Message, state: FSMContext, bot: Bot):
    try:
        await message.answer("Выберите нейросеть 🤖\n\nДоступные для вас нейросети: gpt-4o-mini ✨", reply_markup=kb.main)
        await state.set_state(Generate.selecting_model)  # Возвращаемся к выбору модели
    except Exception as err:
        logger.error(f"Ошибка при смене нейросети: {err}")
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
@router.message(F.text == "Какую выбрать нейросеть 🤔")
async def reset_context(message: Message, state: FSMContext, bot: Bot):
    await message.reply(cmd_message.about_message,
                        parse_mode=ParseMode.MARKDOWN)


@logger.catch
@router.message(F.text.in_(["❎CHATGPT 4-o❎", "✅CHATGPT 4-o-mini✅"]))
async def select_model(message: Message, state: FSMContext):
    model_mapping = {
        "❎CHATGPT 4-o❎": "gpt-4o-2024-08-06",
        "✅CHATGPT 4-o-mini✅": "gpt-4o-mini-2024-07-18"
    }
    model = model_mapping.get(message.text)
    
    await state.update_data(model=model)
    await state.set_state(Generate.text_input)

    await message.answer(f"Вы выбрали {model}\n\nВведите текст для генерации 📝, или отправьте голосое сообщение 🎤:", reply_markup=await kb.change_model(model))


@logger.catch
@router.message(Generate.text_input)
@count_calls()
async def process_generation(message: Message, state: FSMContext, bot: Bot):

    await bot.send_chat_action(message.chat.id, "typing")

    telegram_id = message.from_user.id
    
    # Проверяем время последнего сообщения
    if not await rd.check_time_spacing_between_messages(telegram_id):
        # Если интервал между сообщениями меньше 0.5 секунд, не обрабатываем
        return

    data = await state.get_data()
    model = data.get("model")

    if model is None:
        model = "gpt-4o-mini"

    if message.voice:
            try:
                DOWNLOAD_PATH = './audio_files'

                os.makedirs(DOWNLOAD_PATH, exist_ok=True)
                """Обработчик голосовых сообщений."""
                voice = message.voice

                # Скачиваем голосовое сообщение
                file = await bot.get_file(voice.file_id)
                file_path = f"{DOWNLOAD_PATH}/{file.file_unique_id}.ogg"
                await bot.download_file(file.file_path, file_path)

                # Конвертируем OGG в WAV
                audio = AudioSegment.from_ogg(file_path)
                wav_path = file_path.replace('.ogg', '.wav')
                audio.export(wav_path, format='wav')

                # Транскрибируем аудиофайл
                transcription = await transcribe_audio(wav_path)

                # Проверяем его на ошибки
                transcription_w_err = await correct_text(transcription)

                await message.answer(f"Ваш текст: {transcription_w_err}")

                user_input = transcription_w_err

                # Удаляем временные файлы
                os.remove(file_path)
                os.remove(wav_path)
            except Exception as err:
                logger.error(f"Ошибка с конвертированием аудио в текст: {Exception}")
                await bot.edit_message_text(
                chat_id=waiting_message.chat.id,
                message_id=waiting_message.message_id,
                text=cmd_message.error_message,
                reply_markup=kb.report_an_error
                )
            finally:
                # Проверяем и удаляем оставшиеся файлы
                for root, dirs, files in os.walk(DOWNLOAD_PATH):
                    for file in files:
                        if file.endswith('.ogg') or file.endswith('.wav'):
                            file_to_remove = os.path.join(root, file)
                            if os.path.exists(file_to_remove):
                                try:
                                    os.remove(file_to_remove)
                                except Exception as file_err:
                                    logger.error(f"Не удалось удалить файл {file_to_remove}: {file_err}")

    else:
        user_input = message.text

    # Отправляем сообщение с ожиданием и сохраняем его ID
    waiting_message = await message.reply(f"Модель: {model}\nСреднее время ожидания: всего 5-19 секунд! ⏱🚀\n✨Пожалуйста, подождите✨")

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

    try:
        await bot.send_chat_action(message.chat.id, "typing")
        response = await gpt(user_input, model, telegram_id)
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

        # Цикл for для обработки всех частей списка
        for index, part in enumerate(response_parts):
            try:
                if index == 0:
                    # Отправляем первое сообщение – обновляем старое
                    await bot.edit_message_text(
                        chat_id=waiting_message.chat.id,
                        message_id=waiting_message.message_id,
                        text=part,
                        reply_markup=kb.report_an_error,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    # Отправляем новое сообщение для каждой последующей части
                    await message.reply(
                        part,
                        reply_markup=kb.report_an_error,
                        parse_mode=ParseMode.MARKDOWN
                    )
            except Exception as err:
                logger.error(f"Возникла ошибка с отправкой текста с разметкой markdown: {err}")
                try:
                    if index == 0:
                        # Отправляем первое сообщение – обновляем старое
                        await bot.edit_message_text(
                            chat_id=waiting_message.chat.id,
                            message_id=waiting_message.message_id,
                            text=markdown_decoration.quote(part),
                            reply_markup=kb.report_an_error,
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                    else:
                        # Отправляем новое сообщение для каждой последующей части
                        await message.reply(
                            text=markdown_decoration.quote(part),
                            reply_markup=kb.report_an_error,
                            parse_mode=ParseMode.MARKDOWN_V2
                        )
                except Exception as err:
                    logger.error(f"Возникла ошибка с отправкой текста без разметки markdown: {err}")
                    raise Exception

            # Отправляем информацию о модели, если telegram_id соответствует
            if telegram_id == 857805093:
                await message.answer(
                    f"Model: {model}\nNumber of tokens per input: {count_tokens(user_input)}\nNumber of tokens per output: {count_tokens(part)}",
                )
        
        logger.info(f"Ответ gpt получен и отправлен пользователю: {telegram_id}")
        await state.set_state(Generate.text_input)
        await rd.del_redis_id(telegram_id)
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
@router.message(F.content_type.in_({'text', 'voice'}))
async def error_handling(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state == Generate.waiting_for_response.state:
        await message.reply("Пожалуйста, дождитесь завершения обработки предыдущего запроса. ⏳")
    else:
        await message.reply("Модель не была выбрана, поэтому автоматически выбрана gpt-4o-mini.", reply_markup=await kb.change_model("gpt-4o-mini"))    
        await process_generation(message, state, bot)
