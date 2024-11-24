from aiogram import F, Router, Bot
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from app.logger import file_logger
from app import cmd_message
import app.keyboards as kb
from app.database.db import (
    DatabaseConfig, DatabaseConnection, UserManagement
)
from app.database.db import Models


router = Router()

file_logger()

@router.message(F.text == "Купить запросы 🌟")
async def command_pay(message: Message, state: FSMContext):
    await state.clear()
    await message.reply(cmd_message.prices,
                        reply_markup=kb.assortiment_model,
                        parse_mode=ParseMode.MARKDOWN)

@router.callback_query(lambda callback: callback.data in Models.available_models)
async def select_model(callback: CallbackQuery, state: FSMContext):
    model_name = callback.data
    await state.update_data(model=model_name)
    await callback.message.edit_text(
        f"Вы выбрали модель {model_name}.\n\nПожалуйста, выберите количество запросов.",
        reply_markup=await kb.assortiment_count(model_name)
    )

@router.callback_query(lambda callback: "_" in callback.data)
async def command_pay(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data_parts = callback.data.split("_")
    model_name = data_parts[0]
    request_count = int(data_parts[1])

    await state.update_data(count=request_count)

    price = {
        "gpt-4o": 1.5,
        "gpt-4o-mini": 1,
        "o1-preview": 8,
        "o1-mini": 2
    }

    CURRENCY = "XTR"
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Купить {request_count} запросов к {model_name} 🌟",
        description=cmd_message.attention,
        payload="private",
        currency=CURRENCY,
        prices=[LabeledPrice(label=CURRENCY, amount=request_count*price[model_name])],
        reply_markup=await kb.payment_keyboard(model_name, request_count)
    )
    

@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    await query.answer(True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext) -> None:
    """При успешной оплате, показывает сообщение и добавляет запросы

    Args:
        message (Message): Сообщение пользователя
    """

    data = await state.get_data()
    current_count = data.get("count")
    current_model = data.get("model")

    config = DatabaseConfig()
    connection = DatabaseConnection(config)
    user_manager = UserManagement(connection)

    await user_manager.increases_count_calls(
        telegram_id=message.from_user.id,
        model=current_model,
        count=current_count
    )

    await message.answer(f"Оплата успешно проведена 🎉💳\nТеперь вам доступно *{current_count} запросов*  {current_model}🚀",
                         parse_mode=ParseMode.MARKDOWN)
