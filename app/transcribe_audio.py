import speech_recognition as sr


async def transcribe_audio(file_path: str) -> str:
    """Транскрибирует аудиофайл с помощью SpeechRecognition."""
    recognizer = sr.Recognizer()
    audio = sr.AudioFile(file_path)

    with audio as source:
        audio_data = recognizer.record(source)
    
    try:
        # Используем Google Speech Recognition API
        return recognizer.recognize_google(audio_data, language='ru-RU')
    except sr.UnknownValueError:
        return "Не удалось распознать голос"
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания речи: {e}"
