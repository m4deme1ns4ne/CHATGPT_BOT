from loguru import logger


def file_logger() -> None:
    logger.add("debug.log", format="{time}  {level}  {message}", level="DEBUG", rotation="5 MB", compression="zip")
