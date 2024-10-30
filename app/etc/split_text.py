def split_text(text: str, max_length: int = 4096) -> list:
    """
    Разделяет текст на части не длиннее max_length символов.
    
    :param text: Текст, длину которого нужно поделить на части.
    :param max_length: Длина, которую нужно отрезать.
    :return: Список с текстом, длина каждого куска не больше max_length.
    """
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]
