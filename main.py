import os
import requests
from openai import OpenAI

# Получаем секреты из настроек GitHub
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Настройка клиента OpenRouter (Qwen)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
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
            model="qwen/qwen-2.5-7b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "https://github.com",
                "X-Title": "English Telegram Bot",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Сообщение отправлено!")
    else:
        print(f"Ошибка отправки: {response.text}")

if __name__ == "__main__":
    phrase = generate_phrase()
    if phrase:
        send_telegram_message(phrase)
    else:
        print("Не удалось получить фразу.")
