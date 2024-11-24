from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.logger import file_logger
import app.keyboards as kb
from app.handlers.states import GPTState


router = Router()

file_logger()


@logger.catch
@router.message(F.text.in_(["CHATGPT 4-o", "CHATGPT 4-o-mini", "CHATGPT o1", "CHATGPT o1-mini"]))
async def select_model(message: Message, state: FSMContext):
    from app.database.db import Models

    model = Models.model_mapping_kb.get(message.text)
    
    await state.update_data(model=model)
    await state.set_state(GPTState.text_input)

    await message.answer(f"Вы выбрали {model}\n\nВведите текст для генерации 📝, или отправьте голосое сообщение 🎤:", 
                         reply_markup=await kb.change_model(model))
