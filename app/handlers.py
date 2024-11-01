from aiogram import F, Router, Bot
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.utils.text_decorations import markdown_decoration
from loguru import logger
import os

from logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.database.redis import DatabaseRedis
from app.generators import GPTResponse
from app.database.db import DATABASE
from app.call_count_gpt import GPTUsageHandler
from app.etc.count_token import count_tokens
from app.etc.split_text import split_text
from app.etc.transcribe_audio import transcribe_audio
from app.etc.correct_text import correct_text


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
        return


@router.message(F.text == "Купить запросы 🌟")
async def command_pay(message: Message, state: FSMContext, bot: Bot):
    CURRENCY = "XTR"
    await message.answer_invoice(title="Купить запросы к GPT-4o 🌟",
                                 description=cmd_message.prices,
                                 payload="private",
                                 currency=CURRENCY,
                                 prices=[LabeledPrice(label=CURRENCY, amount=100)],
                                 reply_markup=await kb.payment_keyboard())


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    await query.answer(True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    """При успешной оплате, показывает сообщение и добавляет запросы

    Args:
        message (Message): Сообщение пользователя
    """
    db = DATABASE()
    await message.answer("Оплата успешно проведена 🎉💳\nТеперь вам доступно *100 запросов* CHAT GPT 4o 🚀",
                         parse_mode=ParseMode.MARKDOWN)
    await db.increases_count_calls(
        telegram_id=message.from_user.id,
        model="gpt-4o",
        count=100
    )


@router.message(F.text == "F.A.Q ❓")
async def comman_faq(message: Message, state: FSMContext, bot: Bot):
    await message.reply(cmd_message.faq,
                        parse_mode=ParseMode.MARKDOWN)


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
        db = DATABASE()
        # Очищаем контекст сообщений в базе данных
        await db.clear_message_history(telegram_id)
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
        

@logger.catch
@router.message(F.text == "Какую выбрать нейросеть 🤔")
async def reset_context(message: Message, state: FSMContext, bot: Bot):
    await message.reply(cmd_message.about_message,
                        parse_mode=ParseMode.MARKDOWN)


@logger.catch
@router.message(F.text.in_(["CHATGPT 4-o", "CHATGPT 4-o-mini"]))
async def select_model(message: Message, state: FSMContext):
    model_mapping = {
        "CHATGPT 4-o": "gpt-4o",
        "CHATGPT 4-o-mini": "gpt-4o-mini"
    }
    model = model_mapping.get(message.text)
    
    await state.update_data(model=model)
    await state.set_state(Generate.text_input)

    await message.answer(f"Вы выбрали {model}\n\nВведите текст для генерации 📝, или отправьте голосое сообщение 🎤:", reply_markup=await kb.change_model(model))


@logger.catch
@router.message(Generate.text_input)
async def process_generation(message: Message, state: FSMContext, bot: Bot):

    await bot.send_chat_action(message.chat.id, "typing")

    telegram_id = message.from_user.id

    rd = DatabaseRedis()

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
        hours, minutes, seconds, count = success_and_data[1]
        await message.answer(
            f"*ПРЕВЫШЕН ЛИМИТ ЗАПРОСОВ!*\n\n"
            f"Вы можете использовать до {count} запросов gpt-4o-mini в сутки.\n\n"
            f"Вы сможете использовать gpt снова через {int(hours)} часов, {int(minutes)} минут и {int(seconds)} секунд.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    elif model == "gpt-4o" and not success:
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
                                except Exception as file_err:
                                    logger.error(f"Не удалось удалить файл {file_to_remove}: {file_err}")

    else:
        user_input = message.text

    # Отправляем сообщение с ожиданием и сохраняем его ID
    waiting_message = await message.reply(f"Модель: {model}\nСреднее время ожидания: всего 5-19 секунд! ⏱🚀\n✨Пожалуйста, подождите✨")

    current_state = await state.get_state()

    if current_state == Generate.waiting_for_response.state:
        await message.reply("Пожалуйста, дождитесь завершения обработки предыдущего запроса.")
        return

    await state.set_state(Generate.waiting_for_response)

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
                await message.reply("Не удалось отправить текст в разметке markdown :(")
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
