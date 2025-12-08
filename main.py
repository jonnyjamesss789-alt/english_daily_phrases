import os
import requests
from openai import OpenAI
import time

# --- НАСТРОЙКИ ---
# Ставим тайм-аут 60 секунд. Если нейросеть молчит дольше - отключаемся.
TIMEOUT_SECONDS = 60 

print("--- [1] НАЧАЛО РАБОТЫ СКРИПТА ---")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Проверка наличия ключей (чтобы не гадать)
if not BOT_TOKEN:
    print("ОШИБКА: Нет BOT_TOKEN!")
if not CHANNEL_ID:
    print("ОШИБКА: Нет CHANNEL_ID!")
if not OPENROUTER_API_KEY:
    print("ОШИБКА: Нет OPENROUTER_API_KEY!")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    prompt = (
        "Generate one useful English speaking phrase (B1-B2 level). "
        "Strict format:\n"
        "🇬🇧 **Phrase:** [Phrase]\n"
        "🔊 **Transcription:** [Transcription]\n"
        "🇷🇺 **Translation:** [Russian translation]\n"
        "💡 **Context:** [Short usage context]"
    )
    
    print(f"--- [2] Отправляю запрос в OpenRouter (ждем {TIMEOUT_SECONDS} сек)...")
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            # Попробуем другую модель, если Qwen висит. 
            # Можно вернуть 'qwen/qwen-2.5-7b-instruct:free', если эта не пойдет.
            model="google/gemini-2.0-flash-exp:free", 
            messages=[{"role": "user", "content": prompt}],
            timeout=TIMEOUT_SECONDS
        )
        elapsed = time.time() - start_time
        print(f"--- [3] Ответ получен за {elapsed:.2f} сек!")
        return response.choices[0].message.content
    except Exception as e:
        print(f"!!! ОШИБКА ГЕНЕРАЦИИ !!!: {e}")
        return None

def send_telegram_message(text):
    print("--- [4] Отправляю сообщение в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("--- [5] УСПЕХ! Сообщение отправлено.")
        else:
            print(f"!!! ОШИБКА TELEGRAM !!! Код: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
    except Exception as e:
        print(f"!!! ОШИБКА ПОДКЛЮЧЕНИЯ К TELEGRAM !!!: {e}")

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("Скрипт остановлен из-за отсутствия ключей.")
    else:
        phrase = generate_phrase()
        if phrase:
            print(f"Сгенерированная фраза (первые 50 символов): {phrase[:50]}...")
            send_telegram_message(phrase)
        else:
            print("Фраза пустая, отправка отменена.")

print("--- [КОНЕЦ] ---")
