from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.logger import file_logger
import app.keyboards as kb


router = Router()

file_logger()


class Generate(StatesGroup):
    selecting_model = State()           # Состояние выбора модели
    text_input = State()                # Состояние ожидания текста от пользователя
    waiting_for_response = State()      # Ожидание ответа gpt
    

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

    await message.answer(f"Вы выбрали {model}\n\nВведите текст для генерации 📝, или отправьте голосое сообщение 🎤:", 
                         reply_markup=await kb.change_model(model))
