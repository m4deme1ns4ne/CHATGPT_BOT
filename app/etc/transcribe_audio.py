import speech_recognition as sr
from pydub import AudioSegment
import os


async def transcribe_audio(file_path: str) -> str:
    """
    Транскрибирует аудиофайл с помощью SpeechRecognition.
    
    :param file_path: Путь с нужным аудиофайлом.
    :return: Транскрибация аудиосообщения.
    """
    # Конвертируем OGG в WAV
    audio = AudioSegment.from_ogg(file_path)
    wav_path = file_path.replace('.ogg', '.wav')
    audio.export(wav_path, format='wav')

    recognizer = sr.Recognizer()
    audio = sr.AudioFile(wav_path)

    with audio as source:
        audio_data = recognizer.record(source)
    
    try:
        # Удаляем временные файлы
        os.remove(wav_path)
        os.remove(file_path)
        
        # Используем Google Speech Recognition API
        return recognizer.recognize_google(audio_data, language='ru-RU')
    except sr.UnknownValueError:
        raise Exception("Не удалось распознать голос")
    except sr.RequestError as e:
        raise Exception(f"Ошибка сервиса распознавания речи: {e}")
