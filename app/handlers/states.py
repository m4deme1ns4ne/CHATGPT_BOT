from aiogram.fsm.state import State, StatesGroup


class GPTState(StatesGroup):
    selecting_model = State()           # Состояние выбора модели
    text_input = State()                # Состояние ожидания текста от пользователя
    waiting_for_response = State()      # Состояние ожидания ответа gpt

class PaymentState(StatesGroup):
    model = State()                     # Состояние ожидания модели
    count = State()                     # Состояние ожидания кол-во токенов
