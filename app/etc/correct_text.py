import aiohttp
from loguru import logger

from app.logger import file_logger


@logger.catch
async def correct_text(transcription: str) -> str:
    """
    Улучшает качетсов текста.
    
    :param transcription: Транскрибация аудиосообщения.
    :return: Текст, в котором нету ошибок.
    """ 
    file_logger()
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://speller.yandex.net/services/spellservice.json/checkText"
            params = {"text": transcription,
                      "lang": "ru",
                      "options": "IGNORE_CAPITALIZATION"
                      }
            
            async with session.get(url, params=params) as response:
                corrections = await response.json()
                corrected_text = transcription

                # Вносим исправления в текст
                for correction in corrections:
                    word = correction['word']
                    suggestions = correction.get('s')
                    if suggestions:
                        # Заменяем ошибочное слово на первое предложение из списка
                        corrected_text = corrected_text.replace(word, suggestions[0])
                return corrected_text
    except Exception as err:
        logger.error(f"Ошибка при отправке сообщения Yandex Speller: {err}")
        return transcription
