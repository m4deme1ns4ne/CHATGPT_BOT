def split_text(text: str, max_length: int = 4096) -> list:
    """Разделяет текст на части не длиннее max_length символов."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]
