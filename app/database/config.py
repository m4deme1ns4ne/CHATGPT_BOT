import os


# Конфигурация базы данных
DB_CONFIG = {
    'host': "localhost",
    'user': "root",
    'password': os.getenv("DB_PASSWORD"),
    'db': "chat_gpt_telegram_bot"
}
