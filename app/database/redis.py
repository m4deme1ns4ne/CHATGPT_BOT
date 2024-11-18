import redis
import time
from loguru import logger

from app.logger import file_logger



class DataBaseRedisConfig:
    def __init__(self) -> None:
        self.__host="localhost"
        self.__port=6379
        self.__db=0

    @property
    def host(self):
        return self.__host
    
    @property
    def port(self):
        return self.__port
    
    @property
    def db(self):
        return self.__db
    
class DataBaseRedisMeta(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        """
        Создает единственный экземпляр класса подключения к БД Redis.
        
        :return: Существующий или новый экземпляр класса подключения
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
    
class DataBaseResidClient(metaclass=DataBaseRedisMeta):
    """Управляет подключением к базе данных Redis."""
    def __init__(self, config: DataBaseRedisConfig) -> None:
        self.config = config
        self._redis_client = None

    def get_connection(self):
        """Получения соединения с базой данных Redis"""

        if not self._redis_client:
            self._redis_client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db
            )
        return self._redis_client
    
    def __enter__(self):
        """Метод для входа в контекстный менеджер"""
        return self.get_connection()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Метод для выхода из контекстного менеджера"""
        if self._redis_client:
            self._redis_client.close()

class DatabaseRedisUserManagement:
    def __init__(self, redis_client: DataBaseResidClient) -> None:
        self.client = redis_client

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
            with self.client as client:
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
            with self.client as client:
                client.delete(telegram_id)
        except Exception as err:
            logger.error(f'Пользователь: {telegram_id}. Ошибка при удалении с redis: {err}')
