# ChatGPT Telegram Bot

Telegram bot with ChatGPT integration, supporting both text and voice messages.

You can try it in [telegram](https://t.me/chatgp12e1t_bot).

## 🌟 Key Features

- 💬 Support for GPT 4, 4o-mini, o1, o1-mini
- 🎤 Voice message recognition
- 💾 Save conversation context
- 🔄 Ability to reset context
- 💰 Built-in payment system
- 🎯 Limit the number of requests
- ⏱️ Spam protection

## 🛠 Technologies

- Python 3.12+
- aiogram 3.13+
- OpenAI API
- MySQL
- Redis
- Poetry

## 📋 Requirements

- Python 3.12 or higher
- MySQL server
- Redis server
- OpenAI API key
- Telegram Bot token

## 🚀 Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/chatgpt-telegram-bot.git
```

2. Install dependencies:

```bash
poetry install
```

3. Create a `.env` file and fill it with environment variables or add environment variables with export:

```bash
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
OPENAI_API_KEY="your_openai_api_key"
PROXY="your_proxy_url" (optional)
```

4. Create a MySQL database and run the SQL script to create the necessary tables:

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

## 🎯 Usage

Run the bot:

```bash
python main.py
```

## 📦 Project structure

```plaintext
CHATGPT_BOT/
├── app/
│ ├── database/ # Working with databases
│ ├── etc/ # Helper functions
│ ├── handlers/ # Message handlers
│ ├── cmd_message.py # Text messages
│ ├── generators.py # Generating GPT responses
│ ├── keyboards.py # Bot keyboards
│ └── logger.py # Setup logging
├── main.py # Entry point
├── pyproject.toml # Poetry configuration
└── README.md
```

## 🔒 Security

- Request rate limiting system is used
- Spam protection with Redis
- Secure token storage via environment variables

## 📄 License

This project is distributed under the MIT License, which allows free use, copying, modification and distribution of it with the indication of the original author.

The full text of the license is available in the file [LICENSE](LICENSE).

## 👥 Authors

- Alexander Volzhanin (alexandervolzhanin2004@gmail.com)
