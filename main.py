import os
import logging
from flask import Flask
from openai import OpenAI
import requests

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# Получаем переменные.
# Я переименовал переменную ключа в OPENROUTER_API_KEY для ясности.
# Не забудь поменять имя переменной в настройках Render!
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID") 
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# ВАЖНО: Добавляем base_url для OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    """Генерирует контент через Qwen (OpenRouter)"""
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
            # Здесь указываем конкретную бесплатную модель Qwen
            # Проверь актуальный список бесплатных моделей на openrouter.ai/models
            model="qwen/qwen3-4b:free", 
            messages=[{"role": "user", "content": prompt}],
            # Опционально: указываем название твоего сайта (требование OpenRouter)
            extra_headers={
                "HTTP-Referer": "https://telegram-bot", 
                "X-Title": "English Bot",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenRouter Error: {e}")
        return None

def send_telegram_message(text):
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
        return "Generation failed", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
