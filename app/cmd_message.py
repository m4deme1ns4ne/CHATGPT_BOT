error_message = """
Произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте отправить его снова или сообщите об ошибке, нажан на кнопку ниже. Извините за неудобства! ⚠️
"""

error_message_voice = """
Произошла ошибка при обработке вашего голосового сообщения. Пожалуйста, попробуйте отправить его снова или сообщите об ошибке, нажав на кнопку ниже. Извините за неудобства! ⚠️
"""

start_message = """
👋 Привет! Я ваш умный помощник, готовый помочь вам и отвечать на ваши вопросы!

💡 Я использую передовые технологии от OpenAI — модели GPT-4o и GPT-4o-mini:

🔽 Вы можете выбрать пункт меню ниже, или отправить сообщение, чтобы сразу начать общаться с нейросетью GPT-4o-mini
"""

reset_context_message = "Контекст очищен. Я всё забыл, честно!"

about_message = """
*Модели GPT (Generative Pre-trained Transformer)* — это искусственные интеллектуальные языковые модели, разработанные OpenAI. Они способны генерировать текст, отвечать на вопросы и выполнять другие языковые задачи, обучаясь на больших объемах текстовых данных.

*Вот модели, которые вы можете использовать в данном боте:*

Модель: *GPT-4o*
- Производительность: 
    Высока для сложных задач, учитывает контекст и нюансы.
- Стоимость:
    Средняя, оправдывается качественными результатами.
- Скорость:
    Медленнее из-за сложности задач и объема данных.
- Применение:
    Научные исследования, сложный код, креативный контент.

Модель: *GPT-4o Mini*
- Производительность:
    Ниже, чем у GPT-4o, но эффективна для менее сложных задач без глубокой аналитики.
- Стоимость:
    Значительно дешевле, доступна для малого и среднего бизнеса.
- Скорость:
    Быстрее GPT-4o, подходит для простых и менее ресурсоемких задач.
- Применение:
    Идеальна для обработки текстов, составления резюме, ответов на вопросы и генерации простого контекста.

*По умолчанию стоит модель gpt-4o-mini.*
"""


faq = """
Часто задаваемые вопросы (F.A.Q.) ❓🤔

1. *Что такое нейросети?*
Нейросети — это вычислительные модели, вдохновлённые человеческим мозгом 🧠, которые способны обучаться и выполнять различные задачи, такие как распознавание образов, анализ данных и генерация текста. Наш бот использует такие модели, чтобы понимать и отвечать на ваши запросы.

2. *Какие нейросети можно использовать в боте?*
В нашем боте можно использовать модели GPT-4o и GPT-4o-mini. Они разработаны для обработки естественного языка и предоставления информативных и релевантных ответов на разнообразные запросы. GPT-4o обеспечивает более мощные и сложные ответы, в то время как GPT-4o-mini оптимизирована для быстрого отклика и эффективной работы ⚡️.

3. *Как начать использовать бота?*  
Вы можете просто отправить сообщение в чат с ботом, тогда будет использована модель gpt-4o-mini. Или же, вы можете нажать на кнопку "Выбрать нейросеть", дальше вы можете выбрать нейросеть, доступные нейросети будут присланы отдельным сообщением. После этого можете спокойно общаться с передовыми нейросетями.

4. *Какую информацию я могу получить от бота?*  
Бот может предложить помощь в широком спектре тем, включая обучение 📚, творчество 🎨, программирование 💻, решение задач и многие другие области.

5. *Насколько безопасно общение с ботом?*  
Мы прилагаем все усилия для защиты вашей конфиденциальности 🔒. Однако, как и в случае с любым онлайн-сервисом, рекомендуется избегать передачи личной или конфиденциальной информации 🔍.

6. *Есть ли ограничения на использование бота?*  
Да, бот имеет ограничения на длину и частоту запросов, чтобы обеспечить качество обслуживания для всех пользователей. Если вы столкнетесь с какими-либо ограничениями, попробуйте переформулировать или сократить ваш запрос, или же написать к нам в группу поддержки. Бесплатно можно пользоваться нейросетью gpt-4o-mini, до 50 запросов в неделю.

7. *Как переключаться между нейросетями?*  
В зависимости от сложности и времени отклика вы можете выбрать использование модели GPT-4o для более точных ответов или GPT-4o-mini для более быстрых и легких задач. Выбор осуществляется после нажатия кнопки "Выбрать нейросеть".

8. *К кому обращаться за поддержкой?*  
Если у вас есть вопросы или предложения по улучшению бота, вы можете нажать на кнопку под ответом нейросети "Сообщить об ошибке" или перейти по ссылке в специальную группу для обсуждения: [ссылка](https://t.me/+kHxUGI-eVmhlOTY6) 🔗.
"""


promt = """
Пожалуйста, предоставляйте свои ответы в формате Markdown, пригодном для отображения в Telegram-боте. 
Убедитесь, что вы используете только простые элементы Markdown, такие как **жирный текст**, *курсив*, `вставки кода` и маркированные списки, и всё!. 
Избегайте использования сложных элементов Markdown, которые могут вызвать ошибку в Telegram-боте, таких как таблицы, HTML-теги 
"""



prices = """
В данном телеграмм боте вы можете купить кол-во запросов к разным нейросетям 😉\n
Оплата проходит в валюте telegram stars ⭐️\nКупить их с российской карты вы можете в оффициальном телеграмм боте: @PremiumBot 🤖

Выберите модель, запросы который вы хотите купить:
"""

counts = """ 
Выберите кол-во запросов, которые вы хотите купить:
"""

attention = """ 
Оплатите запросы нажав на кнопку снизу.
"""

watch_code = """
🚀 Вы можете ознакомиться с кодом нашего проекта на [GitHub](https://github.com/m4deme1ns4ne/CHATGPT_BOT)

📜 Этот проект распространяется под лицензией MIT.

😊 Если у вас есть вопросы или предложения, не стесняйтесь обращаться!
"""
