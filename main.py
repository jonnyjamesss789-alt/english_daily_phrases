import os
import requests
from openai import OpenAI
import time

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50

# СПИСОК МОДЕЛЕЙ (Обновил на рабочие версии)
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",   # Сейчас самая стабильная
    "microsoft/phi-3-medium-128k-instruct:free", # Хороший запасной вариант
    "google/gemini-2.0-flash-exp:free",         # Экспериментальная (может меняться)
    "huggingfaceh4/zephyr-7b-beta:free"         # Быстрая
]

print("--- [1] НАЧАЛО РАБОТЫ СКРИПТА ---")

# ПОЛУЧЕНИЕ И ЧИСТКА КЛЮЧЕЙ (Добавил защиту от пробелов)
def get_env_key(key_name):
    value = os.environ.get(key_name)
    if value:
        return str(value).strip() # Удаляем пробелы и энтеры
    return None

BOT_TOKEN = get_env_key("BOT_TOKEN")
CHANNEL_ID = get_env_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_env_key("OPENROUTER_API_KEY")

# Проверка ключей
if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ ОШИБКА: Один из ключей (BOT_TOKEN, CHANNEL_ID, OPENROUTER_API_KEY) пуст!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    prompt = (
        "Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2). "
        "Вся описательная часть (контекст, перевод) должна быть СТРОГО на РУССКОМ языке. "
        "Используй HTML-теги для оформления. "
        "Формат ответа должен быть строго таким:\n\n"
        
        "🇬🇧 <b>Phrase:</b> [Сама фраза]\n\n"
        
        "🔊 <b>Transcription:</b> <code>[Транскрипция]</code>\n\n"
        
        "🇷🇺 <b>Translation:</b> [Перевод фразы на русский]\n\n"
        
        "💡 <i>Context:</i> [Объяснение на русском в 1-2 предложениях, когда это используется]\n\n"
        
        "📝 <b>Example:</b>\n"
        "<blockquote>"
        "— [Пример диалога на английском]\n"
        "— [Продолжение диалога]\n"
        "— (Перевод в скобках)"
        "</blockquote>"
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
            
            content = response.choices[0].message.content
            # Чистим мусор, если модель решила добавить markdown блоки
            content = content.replace("```html", "").replace("```", "").strip()
            return content
            
        except Exception as e:
            print(f"❌ ОШИБКА с моделью {model}: {e}")
            print("Переключаюсь на следующую...")
            time.sleep(1)
            
    return None

def send_telegram_message(text):
    print("--- [3] Отправляю сообщение в Telegram...")
    # Склеиваем URL аккуратно
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
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
    phrase = generate_phrase()
    if phrase:
        send_telegram_message(phrase)
    else:
        print("💀 ВСЕ МОДЕЛИ НЕДОСТУПНЫ. Попробуйте позже.")

print("--- [КОНЕЦ] ---")
