from loguru import logger

def file_logger() -> None:
    # Настройка логгера
    logger.add("debug.log", 
               format="{time} {level} {message}", 
               level="DEBUG", 
               rotation="250 MB",  # Увеличили размер для ротации до 250 MB
               compression="zip",
               retention=0)  # Удаляем старые файлы сразу же после их создания
