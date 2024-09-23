from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Главное меню с выбором модели
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Модель 4-o")],
    [KeyboardButton(text="Модель 4-o-mini")]
],
    resize_keyboard=True,)

# Кнопка для смены модели после её выбора
change_model = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Поменять модель gpt")]
],
    resize_keyboard=True)
