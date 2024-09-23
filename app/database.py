import mysql.connector
from mysql.connector import Error
import os
from loguru import logger
from dotenv import load_dotenv


@logger.catch
# Создание подключения к MySQL серверу
def create_server_connection():
    load_dotenv()
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        # if conn.is_connected():
        #     logger.info("Подключение к серверу MySQL установлено")
        return conn
    except Error as e:
        logger.error(f"Ошибка подключения к серверу MySQL: {e}")
        raise Exception("Не удалось подключиться к серверу базы данных")


@logger.catch
# Проверка и создание базы данных, если она не существует
def create_database():
    try:
        conn = create_server_connection()
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME')}")
        # logger.info(f"База данных '{os.getenv('DB_NAME')}' проверена/создана")
        cursor.close()
        conn.close()
    except Error as e:
        logger.error(f"Ошибка при создании базы данных: {e}")
        raise


@logger.catch
# Создание подключения к MySQL базе данных
def create_connection():
    create_database()  # Сначала проверим/создадим базу данных

    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        # if conn.is_connected():
            # logger.info(f"Подключение к базе данных MySQL '{os.getenv('DB_NAME')}' установлено")
        return conn
    except Error as e:
        logger.error(f"Ошибка подключения к базе данных MySQL: {e}")
        raise Exception("Не удалось подключиться к базе данных")


@logger.catch
# Создание таблицы для хранения сообщений
def init_db():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                role VARCHAR(255) NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        # logger.info("Таблица message_history инициализирована")
    except Error as e:
        logger.error(f"Ошибка создания таблицы в MySQL: {e}")
        raise


@logger.catch
# Функция для добавления сообщения в базу данных
def add_message_to_db(role, content):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        query = 'INSERT INTO message_history (role, content) VALUES (%s, %s)'
        cursor.execute(query, (role, content))
        conn.commit()
        cursor.close()
        conn.close()
        # logger.info(f"Сообщение '{role}' добавлено в базу данных")
    except Error as e:
        logger.error(f"Ошибка при добавлении сообщения в базу данных: {e}")
        raise


@logger.catch
# Функция для получения последних трех сообщений
def get_last_three_messages():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        query = 'SELECT role, content FROM message_history ORDER BY id DESC LIMIT 3'
        cursor.execute(query)
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        return [{"role": role, "content": content} for role, content in reversed(messages)]
    except Error as e:
        logger.error(f"Ошибка при получении последних сообщений: {e}")
        raise


@logger.catch
# Функция для удаления старых сообщений, оставляя только три последних
def clean_old_messages():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        query = 'DELETE FROM message_history WHERE id NOT IN (SELECT id FROM (SELECT id FROM message_history ORDER BY id DESC LIMIT 3) AS t)'
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        # logger.info("Старые сообщения удалены")
    except Error as e:
        logger.error(f"Ошибка при удалении старых сообщений: {e}")
        raise
