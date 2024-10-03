import asyncio
from functools import wraps
import time


# Декоратор для подсчета вызовов функции с обновлением счетчика через reset_interval с использованием asyncio
def count_calls(limit=10, reset_interval=86400):  # 86400 секунд = 24 часа
    def decorator(func):
        call_data = {}

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем ID пользователя (например, telegram_id)
            message = args[0]
            telegram_id = message.from_user.id
            current_time = time.time()

            # Инициализируем данные пользователя, если их нет
            if telegram_id not in call_data:
                call_data[telegram_id] = {'count': 0, 'last_reset': current_time}
                # Запускаем задачу для сброса счетчика вызовов через reset_interval секунд
                asyncio.create_task(reset_call_count(telegram_id, call_data, reset_interval))

            # Увеличиваем счетчик вызовов
            call_data[telegram_id]['count'] += 1

            # Проверяем, превышен ли лимит вызовов
            if call_data[telegram_id]['count'] > limit:
                # Рассчитываем, сколько осталось времени до сброса
                time_since_reset = current_time - call_data[telegram_id]['last_reset']
                time_until_reset = reset_interval - time_since_reset

                # Преобразуем время в удобный формат (часы, минуты, секунды)
                hours, remainder = divmod(time_until_reset, 3600)
                minutes, seconds = divmod(remainder, 60)

                await message.answer(f"ПРЕВЫШЕН ЛИМИТ ЗАПРОСОВ!\n\nВ альфа версии вы можете использовать до 20 запросов gpt-4o-mini в сутки.\n\n Вы сможете использовать gpt снова через {int(hours)} часов, {int(minutes)} минут и {int(seconds)} секунд.")
                return

            # Вызов исходной функции
            return await func(*args, **kwargs)

        return wrapper
    return decorator

# Асинхронная функция для сброса счетчика вызовов
async def reset_call_count(telegram_id, call_data, reset_interval):
    while True:
        await asyncio.sleep(reset_interval)  # Ждем указанное время (в секундах)
        if telegram_id in call_data:
            call_data[telegram_id]['count'] = 0  # Сбрасываем счетчик вызовов
            call_data[telegram_id]['last_reset'] = time.time()  # Обновляем время сброса
