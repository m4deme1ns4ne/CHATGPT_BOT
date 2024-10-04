import redis
import time
from loguru import logger

from logger import file_logger


@logger.catch
def check_time_spacing_between_messages(telegram_id: int) -> bool:

    file_logger()

    try:
        redis_client = redis.Redis(host="localhost", port=6379, db=0)

        current_time = time.time()
        last_message_time = redis_client.get(telegram_id)

        # Проверяем интервал между сообщениями
        if last_message_time is not None and current_time - float(last_message_time) < 0.5:
            # Если интервал между сообщениями меньше 1 секунды, не обрабатываем
            return False
        # Сохраняем текущее время сообщения в Redis
        redis_client.set(telegram_id, current_time)

        # Добавляем таймер исчезновения в размере 3-х минут для переменной
        redis_client.expire(telegram_id, 180)

        return True
    
    except Exception as err:
        logger.error(f'Ошибка при работе с redis: {err}')
        return False

    finally:
        redis_client.close()
