import aiomysql
from datetime import datetime
from dataclasses import dataclass

class DatabaseConfig:
    """Хранит конфигурацию базы данных."""
    def __init__(self):
        self.__user = "root"
        self.__db = "chat_gpt_telegram_bot"
        self.__host = "localhost"
        self.__port = 3306

    @property
    def user(self):
        return self.__user

    @property
    def db(self):
        return self.__db

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

class DatabaseMeta(type):
    """Метакласс для реализации паттерна Singleton при подключении к БД."""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        """
        Создает единственный экземпляр класса подключения к БД.
        
        :return: Существующий или новый экземпляр класса подключения
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=DatabaseMeta):
    """Управляет подключением к базе данных."""
    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self._connection = None

    async def get_connection(self):
        """Получение соединения с базой данных."""
        if not self._connection or self._connection.closed:
            self._connection = await aiomysql.connect(
                user=self.config.user,
                db=self.config.db,
                host=self.config.host,
                port=self.config.port,
                autocommit=True
            )
        return self._connection
    
@dataclass
class Models:
    model_mapping_db = {
        "gpt-4o": "count_gpt_4o",
        "gpt-4o-mini": "count_gpt_4o_mini",
        "gpt-4o-mini-free": "count_gpt_4o_mini_free",
        "o1-preview": "count_gpt_o1",
        "o1-mini": "count_gpt_o1_mini"
    }
    model_mapping_kb = {
        "CHATGPT 4-o": "gpt-4o",
        "CHATGPT 4-o-mini": "gpt-4o-mini",
        "CHATGPT o1": "o1-preview",
        "CHATGPT o1-mini": "o1-mini"
    }
    available_models = [
        "gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"
    ]

class UserManagement:
    """Управляет операциями с пользователями."""
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.model_mapping = Models.model_mapping_db

    async def user_exists(self, telegram_id: int) -> bool:
        """Проверка существования пользователя в таблице users."""
        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 1 FROM users WHERE telegram_id = %s
                """, (telegram_id,))
                result = await cur.fetchone()
                return result is not None

    async def add_user(self, telegram_id: int) -> None:
        """Добавление нового пользователя в таблицы users и gpt_usage."""
        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                # Проверяем наличие пользователя в таблице users
                await cur.execute("SELECT 1 FROM users WHERE telegram_id = %s", (telegram_id,))
                user_exists = await cur.fetchone()

                if not user_exists:
                    # Добавляем пользователя в таблицу users
                    await cur.execute("""
                        INSERT INTO users (telegram_id) VALUES (%s)
                    """, (telegram_id,))
                
                # Проверяем наличие записи в таблице gpt_usage
                await cur.execute(
                    "SELECT 1 FROM gpt_usage WHERE telegram_id = %s", 
                    (telegram_id,))
                usage_exists = await cur.fetchone()

                if not usage_exists:
                    # Добавляем запись в таблицу gpt_usage
                    await cur.execute("""
                        INSERT INTO gpt_usage (telegram_id) VALUES (%s)
                    """, (telegram_id,))
                
            await conn.commit()

    async def get_users_call_data(self, telegram_id: int, model: str):
        selected_model = self.model_mapping.get(model)
        if not selected_model:
            raise ValueError(f"Некорректная модель: {model}")

        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"SELECT {selected_model}, last_reset FROM gpt_usage WHERE telegram_id = %s"
                await cur.execute(query, (telegram_id,))
                return await cur.fetchone() 
            
    async def get_users_call_data(self, telegram_id: int, model: str):
        """
        Получение данных о кол-ве вызовов пользователя из таблицы gpt_usage

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :param model: Модель вызываемой нейросети.
        :return: Данные о кол-ве оставшихся вызовов выбранной модели.
        """

        selected_model = self.model_mapping.get(model)
        
        if not selected_model:
            raise ValueError(f"Некорректная модель: {model}")

        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"SELECT {selected_model}, last_reset FROM gpt_usage WHERE telegram_id = %s"
                await cur.execute(query, (telegram_id,))
                return await cur.fetchone()


    async def update_users_call_data(self, telegram_id: int, model: str, count: int, last_reset: datetime) -> None:
        """
        Обновление данных пользователя в таблице gpt_usage.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :param model: Модель вызываемой нейросети.
        :param count: Количество вызовов модели.
        :param last_reset: Время последнего сброса.
        """

        selected_column = self.model_mapping.get(model)

        if not selected_column:
            raise ValueError(f"Некорректная модель: {model}")

        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE gpt_usage SET {selected_column} = %s, last_reset = %s WHERE telegram_id = %s"
                await cur.execute(query, (count, last_reset, telegram_id))
            await conn.commit()


    async def reset_users_call_data(self, telegram_id: int, count: int, model: str) -> None:
        """
        Сброс счетчика вызовов и обновление времени сброса.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :return: Сбрасывает счётчик вызова бесплатной нейросети
        """
        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE gpt_usage SET %s = %s, last_reset = %s WHERE telegram_id = %s",
                    (model, count, datetime.now(), telegram_id)
                )
            await conn.commit()

    async def decreases_count_calls(self, telegram_id: int, model: str) -> None:
        """
        Уменьшает кол-во вызовов для выбранной нейросети.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :param model: Модель вызываемой нейросети.
        :return: Уменьшает на единицу вызов определённой нейросети по telegram_id
        """

        selected_column = self.model_mapping.get(model)

        if not selected_column:
            raise ValueError(f"Некорректная модель: {model}")

        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE gpt_usage SET {selected_column} = {selected_column} - 1 WHERE telegram_id = %s"
                await cur.execute(query, (telegram_id,))
            await conn.commit()

    async def increases_count_calls(self, telegram_id: int, model: str, count: int) -> None:
        """
        Увеличивает кол-во вызовов для выбранной нейросети.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :param model: Модель вызываемой нейросети.
        :count: Число, на которое увеличивается кол-во вызовов модели.
        :return: Увеличивает на count вызов определённой нейросети по telegram_id
        """

        selected_column = self.model_mapping.get(model)

        if not selected_column:
            raise ValueError(f"Некорректная модель: {model}")

        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE gpt_usage SET {selected_column} = {selected_column} + %s WHERE telegram_id = %s"
                await cur.execute(query, (count, telegram_id,))
            await conn.commit()

class MessageHistory:
    """Управляет историей сообщений."""
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.model_mapping = Models.model_mapping_db

    async def get_message_history(self, telegram_id: int, limit: int = 6) -> list:
        """Получение последних сообщений из истории пользователя."""
        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT role, content FROM message_history 
                    WHERE telegram_id=%s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (telegram_id, limit))
                rows = await cur.fetchall()
                # Порядок сообщений должен быть от старых к новым
                history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
        return history
    
    async def save_message_history(self, telegram_id: int, messages: list) -> None:
        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                # Вставляем новые сообщения
                await cur.executemany("""
                    INSERT INTO message_history (telegram_id, role, content) 
                    VALUES (%s, %s, %s)
                """, [(telegram_id, msg["role"], msg["content"]) for msg in messages])
                
                # Удаляем старые сообщения, оставляя только последние шесть
                await cur.execute("""
                    DELETE FROM message_history
                    WHERE telegram_id = %s AND id NOT IN (
                        SELECT id FROM (
                            SELECT id FROM message_history
                            WHERE telegram_id = %s
                            ORDER BY created_at DESC
                            LIMIT 6
                        ) AS subquery
                    )
                """, (telegram_id, telegram_id))
                
            await conn.commit()

    async def clear_message_history(self, telegram_id: int) -> None:
        """
        Удаление всей истории сообщений пользователя.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :return: Полностью удаляет историю сообщений пользователя 
        в таблице message_history по telegram_id
        """
        async with await self.connection.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    DELETE FROM message_history 
                    WHERE telegram_id = %s
                """, (telegram_id,))
            await conn.commit()
