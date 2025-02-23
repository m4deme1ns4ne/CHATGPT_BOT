# ChatGPT Telegram Bot

###  Docs in in [English](docs/README-eng.md)

Telegram бот с интеграцией ChatGPT, поддерживающий как текстовые, так и голосовые сообщения.

Можете его попробовать в [телеграмме](https://t.me/chatgp12e1t_bot).

## Основные возможности

-  Поддержка моделей GPT 4, 4o-mini, o1, o1-mini
-  Распознавание голосовых сообщений
-  Сохранение контекста диалога
-  Возможность сброса контекста
-  Встроенная система оплаты
-  Ограничение количества запросов
-  Защита от спама

## Технологии

- Python 3.12+
- aiogram 3.13+
- OpenAI API
- MySQL
- Redis
- Poetry
- Yandex Speller

## Требования

- Python 3.12 или выше
- MySQL сервер
- Redis сервер
- OpenAI API ключ
- Telegram Bot токен

## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/chatgpt-telegram-bot.git
```

2. Установите зависимости:

```bash
poetry install
```

3. Создайте файл `.env` и заполните его переменными окружения или добавьте переменные окружения с помощью export:

```bash
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
OPENAI_API_KEY="your_openai_api_key"
PROXY="your_proxy_url" (опционально)
```

4. Создайте базу данных MySQL и выполните SQL-скрипт для создания необходимых таблиц:

```sql
CREATE DATABASE IF NOT EXISTS chat_gpt_telegram_bot;

USE chatgpt_bot;

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
ALTER TABLE gpt_usage
ADD count_gpt_o1 INT DEFAULT 0,
ADD count_gpt_o1_mini INT DEFAULT 0;
ALTER TABLE gpt_usage
MODIFY count_gpt_o1 INT DEFAULT 0 AFTER count_gpt_4o_mini_free,
MODIFY count_gpt_o1_mini INT DEFAULT 0 AFTER count_gpt_o1;
```

## Использование

Запустите бот:

```bash
python main.py
```

## Структура проекта

```plaintext
CHATGPT_BOT/
├── app/
│ ├── database/ # Работа с базами данных
│ ├── etc/ # Вспомогательные функции
│ ├── handlers/ # Обработчики сообщений
│ ├── cmd_message.py # Текстовые сообщения
│ ├── generators.py # Генерация ответов GPT
│ ├── keyboards.py # Клавиатуры бота
│ └── logger.py # Настройка логирования
├── main.py # Точка входа
├── pyproject.toml # Конфигурация Poetry
└── README.md
```

## Безопасность

- Используется система ограничения запросов
- Защита от спама с помощью Redis
- Безопасное хранение токенов через переменные окружения

## Лицензия

Этот проект распространяется на условиях MIT License, что позволяет свободно использовать, копировать, модифицировать и распространять его с указанием оригинального автора.

Полный текст лицензии доступен в файле [LICENSE](LICENSE).

## Авторы

- Alexander Volzhanin (alexandervolzhanin2004@gmail.com)
