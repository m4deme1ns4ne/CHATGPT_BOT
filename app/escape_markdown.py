def escape_markdown(text: str) -> str:

    import re
    
    """
    Экранировать символы в Markdown V2 для передачи в Telegram.
    """
    escape_chars = r'_.*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
