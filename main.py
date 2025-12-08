import os
import requests
from openai import OpenAI
import time

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 40  # Ждем ответа от каждой модели не более 40 сек

# СПИСОК МОДЕЛЕЙ (Бот будет пробовать их по очереди)
MODELS = [
    "google/gemini-2.0-flash-lite-preview-02-05:free", # Самая умная
    "qwen/qwen-2.5-7b-instruct:free",                  # Хорошая альтернатива
    "meta-llama/llama-3.3-70b-instruct:free",          # Мощная Llama
    "microsoft/phi-3-mini-128k-instruct:free"          # Легкая и быстрая
]

print("--- [1] НАЧАЛО РАБОТЫ СКРИПТА ---")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Настройка клиента
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
    
    # Цикл перебора моделей
    for model in MODELS:
        print(f"--- [2] Пробую модель: {model} ...")
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_SECONDS,
                extra_headers={
                    "HTTP-Referer": "https://github.com",
                    "X-Title": "English Bot",
                }
            )
            elapsed = time.time() - start_time
            print(f"✅ УСПЕХ! Модель {model} ответила за {elapsed:.2f} сек!")
            return response.choices[0].message.content
            
        except Exception as e:
            # Если ошибка - просто пишем в лог и идем к следующей модели
            print(f"❌ ОШИБКА с моделью {model}: {e}")
            print("Переключаюсь на следующую...")
            time.sleep(1) # Даем секунду передышки
            
    return None # Если вообще никто не ответил

def send_telegram_message(text):
    print("--- [3] Отправляю сообщение в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("--- [4] ✅ СООБЩЕНИЕ ОТПРАВЛЕНО! Проверяй канал.")
        else:
            print(f"!!! ОШИБКА TELEGRAM !!! Код: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
    except Exception as e:
        print(f"!!! ОШИБКА ПОДКЛЮЧЕНИЯ К TELEGRAM !!!: {e}")

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("Скрипт остановлен: нет ключей.")
    else:
        phrase = generate_phrase()
        if phrase:
            send_telegram_message(phrase)
        else:
            print("💀 ВСЕ МОДЕЛИ НЕДОСТУПНЫ. Попробуйте позже.")

print("--- [КОНЕЦ] ---")
