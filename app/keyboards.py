from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import InlineKeyboardBuilder


most_high_main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Выбрать нейросеть 🧠"), KeyboardButton(text="Купить запросы 🌟")],
    [KeyboardButton(text="Посмотреть код проекта 👀"), KeyboardButton(text="F.A.Q ❓")]
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
    [KeyboardButton(text="CHATGPT o1"), KeyboardButton(text="CHATGPT o1-mini")],
    [KeyboardButton(text="CHATGPT 4-o"), KeyboardButton(text="CHATGPT 4-o-mini")],
    [KeyboardButton(text="Назад ↩️"), KeyboardButton(text="Какую выбрать нейросеть 🤔")]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите модель...")

report_an_error = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Сообщить об ошибке", url="https://t.me/+kHxUGI-eVmhlOTY6")]
    ]
)

assortiment_model = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="CHAT GPT 4o", callback_data="gpt-4o")],
        [InlineKeyboardButton(text="CHAT GPT 4o mini", callback_data="gpt-4o-mini")],
        [InlineKeyboardButton(text="CHATGPT o1", callback_data="o1-preview")],
        [InlineKeyboardButton(text="CHATGPT o1-mini", callback_data="o1-mini")]
    ]
)

async def assortiment_count(model: str):
    assortiment_count = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="100 запросов", callback_data=f"{model}_100")],
            [InlineKeyboardButton(text="300 запросов", callback_data=f"{model}_300")],
            [InlineKeyboardButton(text="500 запросов", callback_data=f"{model}_500")],
            [InlineKeyboardButton(text="1000 запросов", callback_data=f"{model}_1000")]
        ]
    )
    return assortiment_count


async def payment_keyboard(model: str, count: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Купить {count} запросов {model}", pay=True)
    return builder.as_markup()


async def change_model(model: str):
    # Кнопка для смены модели после её выбора
    change_model = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Поменять нейросеть ↩️"),
        KeyboardButton(text="Сброс контекста 🔄")]
    ],
        resize_keyboard=True,
        input_field_placeholder=f"Нейросеть: {model}...")
    return change_model
