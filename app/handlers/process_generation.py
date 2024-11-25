from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.utils.text_decorations import markdown_decoration
from loguru import logger
import os

from app.logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.generators import GPTResponse
from app.call_count_gpt import GPTUsageHandler
from app.etc.count_token import count_tokens
from app.etc.split_text import split_text
from app.etc.transcribe_audio import transcribe_audio
from app.etc.correct_text import correct_text
from app.handlers.states import GPTState
from app.database.redis import (
    DataBaseRedisConfig, DataBaseResidClient, DatabaseRedisUserManagement
)


router = Router()

file_logger()


@logger.catch
@router.message(GPTState.text_input)
async def process_generation(message: Message, state: FSMContext, bot: Bot):

    await bot.send_chat_action(message.chat.id, "typing")

    telegram_id = message.from_user.id

    config = DataBaseRedisConfig()
    client = DataBaseResidClient(config)
    rd = DatabaseRedisUserManagement(client)

    # Проверяем время последнего сообщения
    if not await rd.check_time_spacing_between_messages(telegram_id):
        # Если интервал между сообщениями меньше 0.5 секунд, не обрабатываем
        return

    data = await state.get_data()
    model = data.get("model")

    if model is None:
        model = "gpt-4o-mini"

    usage = GPTUsageHandler(telegram_id)

    success_and_data = await usage.process(model)
    success = success_and_data[0]

    if model == "gpt-4o-mini" and not success:
        days, hours, minutes, seconds, count = success_and_data[1]
        await message.answer(
            f"*ПРЕВЫШЕН ЛИМИТ ЗАПРОСОВ!*\n\n"
            f"Вы можете использовать до {count} запросов gpt-4o-mini в неделю.\n\n"
            f"Вы сможете использовать gpt снова через {int(days)} дней, {int(hours)} часов, {int(minutes)} минут и {int(seconds)} секунд.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    elif not success:
        await message.answer(
            f"*ЗАКОНЧИЛИСЬ ЗАПРОСЫ модели {model}*\n\n"
            f"У вас закончились запросы нейросети {model}.\n" 
            "Вы можете преобрести ещё запросов через кнопку *Купить запросы* 🌟 в главном меню.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

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

                # Транскрибируем аудиофайл
                transcription = await transcribe_audio(file_path)

                # Проверяем его на ошибки и исправляем их
                transcription_w_err = await correct_text(transcription)
                user_input = transcription_w_err

            except Exception as err:
                logger.error(f"Ошибка с конвертированием аудио в текст: {Exception}")
                await message.reply(
                text=cmd_message.error_message_voice,
                reply_markup=kb.report_an_error
                )
                return
            finally:
                # Проверяем и удаляем оставшиеся файлы
                for root, dirs, files in os.walk(DOWNLOAD_PATH):
                    for file in files:
                        if file.endswith('.ogg') or file.endswith('.wav'):
                            file_to_remove = os.path.join(root, file)
                            if os.path.exists(file_to_remove):
                                try:
                                    os.remove(file_to_remove)
                                except Exception as err:
                                    logger.error(f"Не удалось удалить файл {file_to_remove}: {err}")

    else:
        user_input = message.text

    # Отправляем сообщение с ожиданием и сохраняем его ID
    waiting_message = await message.reply(f"Модель: {model}\nСреднее время ожидания: всего 5-19 секунд! ⏱🚀\n✨Пожалуйста, подождите✨")

    current_state = await state.get_state()

    if current_state == GPTState.waiting_for_response.state:
        await message.reply("Пожалуйста, дождитесь завершения обработки предыдущего запроса.")
        return

    await state.set_state(GPTState.waiting_for_response)

    try:
        await bot.send_chat_action(message.chat.id, "typing")
        ai = GPTResponse()
        response = await ai.gpt_answer(question=user_input, 
                                       model_gpt=model, 
                                       telegram_id=telegram_id)
        
    except Exception as err:
        logger.error(f"Ошибка при генерации ответа gpt: {err}")
        await bot.edit_message_text(
            chat_id=waiting_message.chat.id,
            message_id=waiting_message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
        await state.set_state(GPTState.text_input)
        return

    try:
        response_parts = split_text(str(response))

        # Цикл for для обработки всех частей списка
        for i, part in enumerate(response_parts):
            try:
                if i == 0:
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
                await message.reply("Не удалось отправить текст в разметке markdown :(")
                try:
                    if i == 0:
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
                    await bot.edit_message_text(
                        chat_id=waiting_message.chat.id,
                        message_id=waiting_message.message_id,
                        text=cmd_message.error_message,
                        reply_markup=kb.report_an_error
                        )
                    return

            # Отправляем информацию о модели, если telegram_id соответствует 857805093
            if telegram_id == 857805093:
                await message.answer(
                    f"Model: {model}\nNumber of tokens per input: {count_tokens(user_input)}\nNumber of tokens per output: {count_tokens(part)}",
                )
        
        logger.info(f"Ответ gpt получен и отправлен пользователю: {telegram_id}")
        await state.set_state(GPTState.text_input)
        await rd.del_redis_id(telegram_id)
    except Exception as err:
        logger.error(f"Ошибка при отправке сообщения: {err}")
        await bot.edit_message_text(
            chat_id=waiting_message.chat.id,
            message_id=waiting_message.message_id,
            text=cmd_message.error_message,
            reply_markup=kb.report_an_error
            )
        await state.set_state(GPTState.text_input)
        return

@logger.catch
@router.message(F.content_type.in_({'text', 'voice'}))
async def error_handling(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()
    if current_state == GPTState.waiting_for_response.state:
        await message.reply("П��жалуйста, дождитесь завершения обработки предыдущего запроса. ⏳")
    else:
        await message.reply("Модель не была выбрана, поэтому автоматически выбрана gpt-4o-mini.", reply_markup=await kb.change_model("gpt-4o-mini"))    
        await process_generation(message, state, bot)
