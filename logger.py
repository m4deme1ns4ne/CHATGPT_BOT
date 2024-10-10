from loguru import logger


def file_logger() -> None:
    logger.add("debug.log", format="{time}  {level}  {message}", level="DEBUG", rotation="50 MB", compression="zip")
