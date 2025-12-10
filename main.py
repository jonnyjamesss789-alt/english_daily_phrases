import os
import requests
from openai import OpenAI
import time
import random

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50

# ОБНОВЛЕННЫЙ СПИСОК МОДЕЛЕЙ (Проверенные и стабильные на OpenRouter)
# Примечание: 70B модели часто имеют лимиты, поэтому добавлено больше 8B/7B.
MODELS = [
    "meta-llama/llama-3-8b-instruct:free",           # Более легкая и надежная Llama
    "mistralai/mistral-7b-instruct:free",           # Классика, почти всегда доступна
    "google/gemini-2.5-flash:free",                 # Новая версия Gemini Flash
    "qwen/qwen-14b-chat:free",                      # Более крупный Qwen
    "deepseek/deepseek-llm-67b-chat:free"           # Крупная модель для качества
]

# СПИСОК ТЕМ для рандомизации запроса
TOPICS = [
    "Travel", "Business", "Emotions", "Food", "Friendship", "Conflict", 
    "Money", "Health", "Time", "Weather", "Slang", "Idioms", "Hobbies", 
    "Technology", "Relationships", "Education", "Household", 
    "Surprise", "Agreement", "Politeness", "Job Interview", "Movies"
]

print("--- [1] НАЧАЛО РАБОТЫ СКРИПТА ---")

# ФУНКЦИЯ ЧИСТКИ КЛЮЧЕЙ (На всякий случай)
def get_env_key(key_name):
    value = os.environ.get(key_name)
    if value:
        return str(value).strip()
    return None

BOT_TOKEN = get_env_key("BOT_TOKEN")
CHANNEL_ID = get_env_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_env_key("OPENROUTER_API_KEY")

if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ ОШИБКА: Отсутствуют ключи в Secrets!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    # 1. Выбираем случайную тему, чтобы каждый запрос был уникальным
    topic = random.choice(TOPICS)
    print(f"🎲 Тема выбрана: {topic}")
    
    # ИДЕАЛЬНЫЙ ПРОМПТ
    prompt = (
        f"Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2) по теме: {topic}. "
        "Вся описательная часть должна быть СТРОГО на РУССКОМ языке. "
        "Используй HTML-теги. Обязательно делай отступы между блоками. "
        "Формат ответа строго такой:\n\n"
        
        "🇺🇸 <b>Phrase:</b> [Сама фраза]\n\n"
        
        "🔊 <b>Transcription:</b> <i>[Правильная транскрипция с транслитерацией русскими буквами.]</i>\n\n"
        
        "🇷🇺 <b>Translation:</b> [Перевод фразы]\n\n"
        
        "📃 <b>Context:</b> <i>[Объяснение на русском в 1-2 предложениях, когда это используется]</i>\n\n"
        
        "📝 <b>Example:</b>\n"
        "<blockquote>"
        "— [Пример диалога на английском] (в скобках перевод)\n"
        "— [Продолжение диалога] (в скобках перевод)\n"
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
                extra_headers={"HTTP-Referer": "https://github.com", "X-Title": "English Bot"}
            )
            elapsed = time.time() - start_time
            print(f"✅ УСПЕХ! Модель {model} ответила за {elapsed:.2f} сек!")
            
            content = response.choices[0].message.content
            # Убираем внешние блоки кода, которые иногда добавляет LLM
            content = content.replace("```html", "").replace("```", "").strip() 
            return content
            
        except Exception as e:
            # Выводим код ошибки для диагностики (например, 429 или 404)
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
        "parse_mode": "HTML" # Режим HTML включен
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("--- [4] ✅ СООБЩЕНИЕ ОТПРАВЛЕНО! Проверяй канал.")
        else:
            # Печатаем ответ сервера, чтобы понять причину ошибки Telegram
            print(f"!!! ОШИБКА TELEGRAM !!! Код: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            
    except Exception as e:
        print(f"!!! ОШИБКА ПОДКЛЮЧЕНИЯ К TELEGRAM !!!: {e}")

if __name__ == "__main__":
    phrase = generate_phrase()
    if phrase:
        # Добавляем эмодзи в начало, если их нет, для красоты
        if not phrase.startswith(("🇺🇸", "🇬🇧")):
             phrase = "🇺🇸 " + phrase
        send_telegram_message(phrase)
    else:
        print("💀 ВСЕ МОДЕЛИ НЕДОСТУПНЫ. Попробуйте позже.")

print("--- [КОНЕЦ] ---")
