import os
import requests
from openai import OpenAI
import time
import random

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50

# ОБНОВЛЕННЫЙ И СТАБИЛЬНЫЙ СПИСОК МОДЕЛЕЙ (убраны 404/400 ошибки)
MODELS = [
    "mistralai/mistral-7b-instruct:free",           # Самая стабильная (именно она у вас работала)
    "google/gemma-7b-it:free",                      # Легкая и новая
    "meta-llama/llama-3-8b-instruct:free",          # Включаем снова, иногда работает
    "qwen/qwen-14b-chat:free",                      # Запасная крупная модель
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

# --- КЛЮЧИ ---
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
    topic = random.choice(TOPICS)
    print(f"🎲 Тема выбрана: {topic}")
    
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
            content = response.choices[0].message.content
            
            # ВАЖНОЕ ИЗМЕНЕНИЕ: Убираем возможные внешние теги, которые могут сломать HTML-парсер
            content = content.replace("```html", "").replace("```", "").strip() 
            
            # УСПЕХ: Если мы дошли досюда, значит, все хорошо. Выходим.
            print(f"✅ УСПЕХ! Модель {model} ответила за {elapsed:.2f} сек!")
            return content 
            
        except Exception as e:
            print(f"❌ ОШИБКА с моделью {model}: {e}")
            print("Переключаюсь на следующую...")
            time.sleep(1)
            
    return None # Если цикл завершился и ни одна модель не вернула content

def send_telegram_message(text):
    print("--- [3] Отправляю сообщение в Telegram...")
    # Добавляем эмодзи в начало, если их нет, для красоты
    if not text.startswith(("🇺🇸", "🇬🇧")):
        text = "🇺🇸 " + text
        
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
        # Эта ошибка теперь означает, что НИ ОДНА модель не сработала
        print("💀 ВСЕ МОДЕЛИ НЕДОСТУПНЫ (или лимиты). Попробуйте позже.")

print("--- [КОНЕЦ] ---")
