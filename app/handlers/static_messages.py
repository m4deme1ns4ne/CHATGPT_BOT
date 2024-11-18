from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from loguru import logger

from app.logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.handlers.states import GPTState


router = Router()

file_logger()


@logger.catch
@router.message(F.text.in_(["Вернуться в главное меню ↩️", "/start", "Назад ↩️"]))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await message.answer(cmd_message.start_message, reply_markup=kb.most_high_main)
    await state.clear()  # Очистка состояния при старте
    await state.set_state(GPTState.selecting_model)  # Устанавливаем состояние выбора модели

@logger.catch
@router.message(F.text == "Какую выбрать нейросеть 🤔")
async def which_neural_network_to_choose(message: Message):
    await message.reply(cmd_message.about_message,
                        parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "F.A.Q ❓")
async def comman_faq(message: Message, state: FSMContext, bot: Bot):
    await message.reply(cmd_message.faq,
                        parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "Посмотреть код проекта 👀")
async def watch_code(message: Message):
    await message.reply(cmd_message.watch_code,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
