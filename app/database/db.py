import aiomysql
from datetime import datetime


"""
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE gpt_usage (
    telegram_id BIGINT PRIMARY KEY,
    count_gpt_4o INT DEFAULT 0,
    count_gpt_4o_mini INT DEFAULT 0,
    count_gpt_4o_mini_free INT DEFAULT 0,
    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE message_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT,
    role VARCHAR(255),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telegram_id_created_at (telegram_id, created_at)
);
"""


class DATABASE:
    def __init__(self):
        self.user = "root"
        self.db = "chat_gpt_telegram_bot"
        self.host = "localhost"
        self.port = 3306
        self.model_mapping = {
            "gpt-4o": "count_gpt_4o",
            "gpt-4o-mini": "count_gpt_4o_mini",
            "gpt-4o-mini-free": "count_gpt_4o_mini_free"
        }


    async def get_connection(self) -> None:
        """
        Получение соединения с базой данных.

        """
        return await aiomysql.connect(user=self.user, db=self.db,
                                      host=self.host, port=self.port)


    async def user_exists(self, telegram_id: int) -> bool:
        """
        Проверка существования пользователя в таблице users.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT 1 FROM users WHERE telegram_id = %s
                """, (telegram_id,))
                result = await cur.fetchone()
                return result is not None


    async def add_user(self, telegram_id: int) -> None:
        """
        Добавление нового пользователя в таблицы users и gpt_usage.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        """
        async with await self.get_connection() as conn:
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


    async def get_message_history(self, telegram_id: int, limit: int = 6) -> list:
        """
        Получение последних сообщений из истории пользователя.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :param limit: Лимиты истории сообщений.
        :return: История сообщений в виде списка.
        """
        async with await self.get_connection() as conn:
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
        """
        Сохранение новых сообщений в историю пользователя и удаление старых.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :param messages: Новое сообщение от пользователя.
        :return: Сохраняет новые сообщения в таблицу message_history по telegram_id,
        а так же удаляет последнии сообщения, оставляя последнии шесть.
        """
        async with await self.get_connection() as conn:
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
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    DELETE FROM message_history 
                    WHERE telegram_id = %s
                """, (telegram_id,))
            await conn.commit()


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
        
        async with await self.get_connection() as conn:
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

        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE gpt_usage SET `{selected_column}` = %s, last_reset = %s WHERE telegram_id = %s"
                await cur.execute(query, (count, last_reset, telegram_id))
            await conn.commit()


    async def reset_users_call_data(self, telegram_id: int, count: int, model: str) -> None:
        """
        Сброс счетчика вызовов и обновление времени сброса.

        :param telegram_id: Уникальный идентификатор пользователя в Телеграмм.
        :return: Сбрасывает счётчик вызова бесплатной нейросети
        """
        async with await self.get_connection() as conn:
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

        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE gpt_usage SET `{selected_column}` = `{selected_column}` - 1 WHERE telegram_id = %s"
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

        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE gpt_usage SET `{selected_column}` = `{selected_column}` + {count} WHERE telegram_id = %s"
                await cur.execute(query, (telegram_id,))
            await conn.commit()
