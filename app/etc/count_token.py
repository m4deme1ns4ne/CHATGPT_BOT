import tiktoken


def count_tokens(text: str, model_name:str = 'gpt-4-o-mini') -> int:
    """
    Считает кол-во токенов в тексте.
    
    :param text: Текст, кол-во токенов, которого нужно посчитать.
    :param model: Используемая модель для подсчёта токенов, по умолчанию gpt-4-o-mini.
    :return: Число токенов.
    """
    # Получаем кодировщик для указанной модели
    encoding = tiktoken.encoding_for_model(model_name)
    
    # Кодируем текст и получаем список токенов
    tokens = encoding.encode(text)
    
    # Возвращаем количество токенов
    return len(tokens)
