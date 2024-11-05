import asyncio
from datetime import datetime
from app.database.db import DATABASE
from loguru import logger

from app.logger import file_logger


file_logger()

class GPTUsageHandler:
    """
    Класс для обработки использования модели GPT.
    """
    def __init__(self, telegram_id: int) -> None:
        self.telegram_id = telegram_id
        self.db = DATABASE()
        self.current_time = datetime.now()
        self.free_model = "gpt-4o-mini-free"
        self.gpt_4o_mini = "gpt-4o-mini"
        self.gpt_4o = "gpt-4o"


    @logger.catch
    async def process(self, model: str) -> tuple[bool, tuple]:
        """
        Обработка запроса к модели.

        :param model: Название модели для использования.
                      Может быть "gpt-4o" или другая модель.

        :return: Результат обработки запроса. Возвращает кортеж,
                 где первый элемент - успешность операции (True/False),
                 второй элемент - данные о времени и кол-ве вызово в виде кортежа.
                 Если операция неуспешна, возвращается оставшееся время до сброса лимита.
                 Если успешна, возвращаются None значения.
        """
        if model == "gpt-4o":
            result = await self.count_gpt(self.gpt_4o)
        else:
            result = await self.count_gpt_4o_mini_free()
        return result
    

    @logger.catch
    async def count_gpt(self, model: str) -> tuple[bool]:
        """
        Обработка вызова платной версии моделей gpt.

        :param model: модель gpt

        :return: Результат обработки запроса. Возвращает кортеж,
                      где первый элемент - успешность операции (True/False),
                      второй элемент - данные о времени и кол-ве вызово в виде кортежа.
                      Если операция неуспешна, возвращается оставшееся время до сброса лимита.
                      Если успешна, возвращаются None значения.
        """
        if not await self.db.user_exists(self.telegram_id):
            await self.db.add_user(self.telegram_id)
            # Если данных нет, создаем запись для пользователя с текущим временем
            await self.db.update_users_call_data(telegram_id=self.telegram_id, 
                                                 model=model, 
                                                 count=0,
                                                 last_reset=self.current_time)
            return (False,)

        else:
            call_count, last_reset = await self.db.get_users_call_data(self.telegram_id, model)

            if call_count > 0:
                # Преобразуем last_reset в тип datetime, если необходимо
                if isinstance(last_reset, float):
                    last_reset = datetime.fromtimestamp(last_reset)

                await self.db.decreases_count_calls(self.telegram_id, model)
                call_count -= 1

                await self.db.update_users_call_data(telegram_id=self.telegram_id, 
                                                    model=model, 
                                                    count=call_count,
                                                    last_reset=last_reset)
                return (True,)
            
            else:
                return (False,)


    @logger.catch
    async def count_gpt_4o_mini_free(self, count: int=50, reset_interval: datetime=604800) -> tuple[bool, tuple]:
        """
        Обработка вызова бесплатной и платной версии модели gpt-4o-mini 
        с учетом ограничений по количеству запросов.

        :param count: Максимальное количество разрешенных вызовов за интервал времени.
                      По умолчанию равно 50.   
        :param reset_interval: Интервал времени (в секундах), после которого счетчик обнуляется. 
                      По умолчанию равно 604800 (7 дней)
        :return: Результат обработки запроса. Возвращает кортеж,
                      где первый элемент - успешность операции (True/False),
                      второй элемент - данные о времени и кол-ве вызово в виде кортежа.
                      Если операция неуспешна, возвращается оставшееся время до сброса лимита.
                      Если успешна, возвращаются None значения.
        """
        if not await self.db.user_exists(self.telegram_id):
            call_count = count - 1
            # Добавляем пользователя в базу данных
            await self.db.add_user(self.telegram_id)
            # Если данных нет, создаем запись для пользователя с текущим временем
            await self.db.update_users_call_data(telegram_id=self.telegram_id, 
                                                 model=self.free_model, 
                                                 count=call_count,
                                                 last_reset=self.current_time)
            asyncio.create_task(self.reset_call_count(reset_interval, count))
            return (True,)
        else:
            # Получаем данные пользователя из базы данных
            call_count, last_reset = await self.db.get_users_call_data(self.telegram_id, self.free_model)

            # Преобразуем last_reset в тип datetime, если необходимо
            if isinstance(last_reset, float):
                last_reset = datetime.fromtimestamp(last_reset)

            time_since_reset = (self.current_time - last_reset).total_seconds()

            # Если прошло достаточно времени, сбрасываем счетчик
            if time_since_reset >= reset_interval:
                call_count = count
                last_reset = self.current_time

            # Проверяем, превышен ли лимит вызовов в бесплатной модели
            if call_count <= 0:
                # Проверяем, превышен ли лимит вызовов в платной модели
                result = await self.count_gpt(self.gpt_4o_mini)
                if not result[0]:
                    time_until_reset = reset_interval - time_since_reset
                    hours, remainder = divmod(time_until_reset, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    return (False, (hours, minutes, seconds, count))
                return (True,)

            # Уменьшаем счетчик вызовов
            await self.db.decreases_count_calls(self.telegram_id, self.free_model)
            call_count -= 1

            # Обновляем данные пользователя в базе
            await self.db.update_users_call_data(telegram_id=self.telegram_id, 
                                                 model=self.free_model, 
                                                 count=call_count, 
                                                 last_reset=last_reset)
            return (True,)


    async def reset_call_count(self, reset_interval: datetime, count: int):
        """
        Cброс счетчика вызовов в бесплатной модели.

        :param reset_interval: Интервал времени (в секундах), 
                               через который происходит сброс счетчика.
        :param count: Количество вызовов, на которое будет установлен счетчик после сброса.
        """
        
        await asyncio.sleep(reset_interval)  # Ждем указанное время (в секундах)
        
        # Сбрасываем счетчик вызовов для пользователя
        await self.db.reset_users_call_data(telegram_id=self.telegram_id,
                                            count=count,
                                            model=self.free_model)
