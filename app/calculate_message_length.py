def calculate_message_length(message):
    length = 0
    for char in message:
        # Проверяем, является ли символ эмодзи или другим многобайтовым символом
        if len(char.encode('utf-8')) > 1:
            length += 2  # Каждый такой символ в Телеграме может считаться за два
        else:
            length += 1
    return length
