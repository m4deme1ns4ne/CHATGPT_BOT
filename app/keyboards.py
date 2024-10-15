from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)


most_high_main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Подписка 🌟"), KeyboardButton(text="F.A.Q ❓")],
    [KeyboardButton(text="Выбрать нейросеть 🧠")]
    ],
    resize_keyboard=True
    )

back = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Вернуться в главное меню ↩️")]
    ],
    resize_keyboard=True,
    )

# Главное меню с выбором модели
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❎CHATGPT 4-o❎"), KeyboardButton(text="✅CHATGPT 4-o-mini✅")],
    [KeyboardButton(text="Назад ↩️"), KeyboardButton(text="Какую выбрать нейросеть 🤔")]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите модель...")

async def change_model(model: str):
    # Кнопка для смены модели после её выбора
    change_model = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Поменять нейросеть ↩️"),
        KeyboardButton(text="Сброс контекста 🔄")]
    ],
        resize_keyboard=True,
        input_field_placeholder=f"Нейросеть: {model}...")
    return change_model

report_an_error = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Сообщить об ошибке", url="https://t.me/+kHxUGI-eVmhlOTY6")]
    ]
)
