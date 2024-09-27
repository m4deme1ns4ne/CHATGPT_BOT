import aiomysql
import os


"""
CREATE TABLE users (
    telegram_id INT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE message_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id INT,
    role VARCHAR(255),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telegram_id_created_at (telegram_id, created_at),
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);
"""

async def get_connection():
    """Получение соединения с базой данных."""
    return await aiomysql.connect(user="root", password=os.getenv("DB_PASSWORD"), db="chat_gpt_telegram_bot")


async def user_exists(telegram_id: int) -> bool:
    """Проверка, существует ли пользователь в таблице users."""
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT 1 FROM users WHERE telegram_id = %s
            """, (telegram_id,))
            result = await cur.fetchone()
            return result is not None
    finally:
        conn.close()


async def add_user(telegram_id: int):
    """Добавление нового пользователя в таблицу users."""
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO users (telegram_id) VALUES (%s)
            """, (telegram_id,))
            await conn.commit()
    finally:
        conn.close()


async def get_message_history(telegram_id: int, limit: int = 2):
    """Получение последних сообщений из истории пользователя."""
    conn = await get_connection()
    try:
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
    finally:
        conn.close()
    return history


async def save_message_history(telegram_id: int, messages: list):
    """Сохранение новых сообщений в историю пользователя и удаление старых."""
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            # Вставляем новые сообщения
            await cur.executemany("""
                INSERT INTO message_history (telegram_id, role, content) 
                VALUES (%s, %s, %s)
            """, [(telegram_id, msg["role"], msg["content"]) for msg in messages])
            
            # Удаляем старые сообщения, оставляя только последние два
            await cur.execute("""
                DELETE FROM message_history
                WHERE telegram_id = %s AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM message_history
                        WHERE telegram_id = %s
                        ORDER BY created_at DESC
                        LIMIT 2
                    ) AS subquery
                )
            """, (telegram_id, telegram_id))
            
            await conn.commit()
    finally:
        conn.close()


async def clear_message_history(telegram_id: int):
    """Удаление всей истории сообщений пользователя."""
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                DELETE FROM message_history 
                WHERE telegram_id = %s
            """, (telegram_id,))
            await conn.commit()
    finally:
        conn.close()