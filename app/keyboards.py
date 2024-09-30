from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Главное меню с выбором модели
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌Модель 4-o❌")],
    [KeyboardButton(text="✅Модель 4-o-mini✅")]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите модель...")

async def change_model(model: str):
    # Кнопка для смены модели после её выбора
    change_model = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Поменять модель gpt"),
        KeyboardButton(text="Сброс контекста")]
    ],
        resize_keyboard=True,
        input_field_placeholder=f"Модель {model}...")
    return change_model
