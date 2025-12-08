import os
import requests
from openai import OpenAI
import time

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 40

# СПИСОК МОДЕЛЕЙ (Оставляем, так как это спасло нас от ошибки 429)
MODELS = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free"
]

print("--- [1] НАЧАЛО РАБОТЫ СКРИПТА ---")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    # Обновленный промпт для красивого оформления
    prompt = (
        "Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2). "
        "Вся описательная часть (контекст, перевод) должна быть СТРОГО на РУССКОМ языке. "
        "Сделай отступы (пустые строки) между пунктами. "
        "Формат ответа должен быть в точности таким:\n\n"
        
        "🇬🇧 **Phrase:** [Сама фраза]\n\n"
        
        "🔊 **Transcription:** [Транскрипция]\n\n"
        
        "🇷🇺 **Translation:** [Перевод фразы на русский]\n\n"
        
        "💡 **Context:** [Объясни на русском в 1-2 предложениях, в какой ситуации эту фразу используют]\n\n"
        
        "📝 **Example:**\n"
        "— [Пример предложения или мини-диалога на английском с этой фразой]\n"
        "— ([Перевод этого примера на русский])"
    )
    
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
            print(f"❌ ОШИБКА с моделью {model}: {e}")
            print("Переключаюсь на следующую...")
            time.sleep(1)
            
    return None

def send_telegram_message(text):
    print("--- [3] Отправляю сообщение в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown" # Важно для жирного текста
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
