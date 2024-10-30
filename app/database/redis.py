import redis
import time
from loguru import logger

from logger import file_logger


class DatabaseRedis:
    def __init__(self) -> None:
        """
        Устанавливает соединение с сервером Redis, используя заданные параметры хоста, порта и индекса базы данных.
        
        Создает объект `redis_client` для дальнейшего взаимодействия с базой данных.
        """
        self.redis_client = redis.Redis(host="localhost", 
                                port=6379, 
                                db=0)


    @logger.catch
    async def check_time_spacing_between_messages(self, telegram_id: int) -> bool:
        """
        Проверяет интервал между сообщениями пользователя по его Telegram ID.

        Если интервал меньше 0.5 секунд, возвращает False и не обрабатывает сообщение. 
        В противном случае сохраняет текущее время сообщения и устанавливает таймер на 5 минут.

        :param telegram_id: ID пользователя в Telegram.
        
        :return: True, если сообщение может быть обработано; False в противном случае.

        Исключения:
            Логирует ошибки при работе с базой данных Redis.
         
         """
        
        file_logger()

        try:
            with self.redis_client as client:
                current_time = time.time()
                last_message_time = client.get(telegram_id)

                # Проверяем интервал между сообщениями
                if last_message_time is not None and current_time - float(last_message_time) < 0.5:
                    # Если интервал между сообщениями меньше 1 секунды, не обрабатываем
                    return False
                
                # Сохраняем текущее время сообщения в Redis
                client.set(telegram_id, current_time)

                # Добавляем таймер исчезновения в размере 5 минут для переменной
                client.expire(telegram_id, 300)

                return True
            
        except Exception as err:
            logger.error(f'Пользователь: {telegram_id}. Ошибка при работе с redis: {err}')
            return False


    @logger.catch
    async def del_redis_id(self, telegram_id: int) -> None:
        """
        Удаляет запись пользователя из базы данных Redis по его Telegram ID.

        :param telegram_id: ID пользователя в Telegram.

        Исключения:
            Логирует ошибки при удалении записи из базы данных Redis.

        """

        file_logger()

        try:
            with self.redis_client as client:
                client.delete(telegram_id)
        except Exception as err:
            logger.error(f'Пользователь: {telegram_id}. Ошибка при удалении с redis: {err}')
