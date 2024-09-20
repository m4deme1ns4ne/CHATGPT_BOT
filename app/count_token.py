import tiktoken


def count_tokens(text, model_name='gpt-4-o-mini'):
    # Получаем кодировщик для указанной модели
    encoding = tiktoken.encoding_for_model(model_name)
    
    # Кодируем текст и получаем список токенов
    tokens = encoding.encode(text)
    
    # Возвращаем количество токенов
    return len(tokens)
