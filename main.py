import os
import logging
from flask import Flask
from openai import OpenAI
import requests

# Инициализация Flask приложения
app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем ключи из переменных окружения (настроим их на Render позже)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID") 
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_phrase():
    """Генерирует контент через OpenAI"""
    prompt = (
        "Сгенерируй одну разговорную фразу на английском (B1-B2). "
        "Дай ответ СТРОГО в таком формате, без лишних слов:\n"
        "🇬🇧 **Phrase:** [Фраза]\n"
        "🔊 **Transcription:** [Транскрипция]\n"
        "🇷🇺 **Translation:** [Перевод]\n"
        "💡 **Context:** [1 предложение, где используется]"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Или gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        return None

def send_telegram_message(text):
    """Отправляет сообщение в канал через обычный запрос"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    return response.json()

@app.route('/')
def index():
    return "Bot is alive!", 200

# Эту ссылку будет дергать Cron-job
@app.route('/trigger_post', methods=['GET'])
def trigger_post():
    phrase = generate_phrase()
    if phrase:
        result = send_telegram_message(phrase)
        if result.get("ok"):
            return "Message sent successfully", 200
        else:
            return f"Telegram Error: {result}", 500
    else:
        return "OpenAI generation failed", 500

if __name__ == '__main__':
    # Эта часть нужна для локального запуска, на сервере используется gunicorn
    app.run(host='0.0.0.0', port=5000)
