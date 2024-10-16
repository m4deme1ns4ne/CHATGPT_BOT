import asyncio
from datetime import datetime
from functools import wraps
import app.database.db as db
from loguru import logger

from logger import file_logger


# Декоратор для подсчета вызовов функции с использованием MySQL
@logger.catch
def count_calls(limit=10, reset_interval=86400):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            file_logger()
            try:
                # Получаем telegram_id пользователя
                message = args[0]
                telegram_id = message.from_user.id

                if telegram_id == 857805093:
                    await db.reset_users_call_data(857805093)

                current_time = datetime.now()  # Используем datetime для записи времени

                # Получаем данные пользователя из базы данных
                result = await db.get_users_call_data(telegram_id)

                if result is None:
                    # Если данных нет, создаем запись для пользователя с текущим временем
                    await db.update_users_call_data(telegram_id, 1, current_time)
                    asyncio.create_task(reset_call_count(telegram_id, reset_interval))
                else:
                    call_count, last_reset = result

                    # Преобразуем last_reset в тип datetime, если необходимо
                    if isinstance(last_reset, float):
                        last_reset = datetime.fromtimestamp(last_reset)

                    time_since_reset = (current_time - last_reset).total_seconds()

                    # Если прошло достаточно времени, сбрасываем счетчик
                    if time_since_reset >= reset_interval:
                        call_count = 0
                        last_reset = current_time

                    # Увеличиваем счетчик вызовов
                    call_count += 1
                    await db.increase_call_count(telegram_id)

                    # Проверяем, превышен ли лимит вызовов
                    if call_count > limit:
                        time_until_reset = reset_interval - time_since_reset
                        hours, remainder = divmod(time_until_reset, 3600)
                        minutes, seconds = divmod(remainder, 60)

                        await message.answer(
                            f"ПРЕВЫШЕН ЛИМИТ ЗАПРОСОВ!\n\n"
                            f"Вы можете использовать до {limit} запросов gpt-4o-mini в сутки.\n\n"
                            f"Вы сможете использовать gpt снова через {int(hours)} часов, {int(minutes)} минут и {int(seconds)} секунд."
                        )
                        await message.answer_animation(
                            animation='CgACAgIAAxkBAAIJ4GcK5kGcn4RhiVGJYdnQwMuITvSBAAKXUgAC0zoIS7nqeg0TrWDKNgQ'
                        )
                        return

                    # Обновляем данные пользователя в базе
                    await db.update_users_call_data(telegram_id, call_count, last_reset)
            except Exception as err:
                logger.error(f"Ошибка с подсчётом количества вызовов: {err}")
            # Вызов исходной функции
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Асинхронная функция для сброса счетчика вызовов
async def reset_call_count(telegram_id, reset_interval):
    await asyncio.sleep(reset_interval)  # Ждем указанное время (в секундах)
    # Сбрасываем счетчик вызовов для пользователя
    await db.reset_users_call_data(telegram_id)
