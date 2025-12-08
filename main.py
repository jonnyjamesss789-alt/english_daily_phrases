import os
import requests
from openai import OpenAI
import time
import random

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50
HISTORY_FILE = "history.txt"

# СПИСОК МОДЕЛЕЙ
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "google/gemini-2.0-flash-exp:free"
]

# СПИСОК ТЕМ
TOPICS = [
    "Travel & Airports", "Business & Office", "Emotions", "Food",
    "Friendship", "Conflict", "Money", "Health", "Time", "Weather",
    "Slang", "Idioms", "Hobbies", "Technology", "Relationships", 
    "Driving", "Education", "Household", "Surprise", "Agreement", 
    "Politeness", "Job Interview", "Movies", "Social Media"
]

print("--- [1] НАЧАЛО РАБОТЫ СКРИПТА ---")

def get_env_key(key_name):
    value = os.environ.get(key_name)
    if value:
        return str(value).strip()
    return None

BOT_TOKEN = get_env_key("BOT_TOKEN")
CHANNEL_ID = get_env_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_env_key("OPENROUTER_API_KEY")

if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ ОШИБКА: Отсутствуют ключи!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- ФУНКЦИИ ИСТОРИИ ---
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f.readlines()]
    except Exception:
        return []

def save_to_history(phrase_text):
    # Пытаемся вытащить фразу между Phrase: и Transcription:
    try:
        # Упрощенный поиск для сохранения
        if "Phrase:" in phrase_text:
            parts = phrase_text.split("Phrase:")[1]
            clean_phrase = parts.split("Transcription:")[0].split("🔊")[0].strip()
            # Убираем HTML теги если остались
            clean_phrase = clean_phrase.replace("<b>", "").replace("</b>", "").strip()
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(clean_phrase + "\n")
            print(f"💾 Фраза '{clean_phrase}' сохранена в историю.")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить в историю: {e}")

# --- ФОРМАТИРОВАНИЕ ---
def format_content(content):
    content = content.replace("```html", "").replace("```", "").strip()
    
    # Сначала чистим от старых тегов
    clean_map = {
        "<b>Phrase:</b>": "Phrase:", "<b>Transcription:</b>": "Transcription:",
        "<b>Translation:</b>": "Translation:", "<b>Context:</b>": "Context:", 
        "<b>Example:</b>": "Example:"
    }
    for k, v in clean_map.items():
        content = content.replace(k, v)

    # Применяем красивые теги и смайлы
    replacements = {
        "Phrase:": "🇺🇸 <b>Phrase:</b>",
        "Transcription:": "🔊 <b>Transcription:</b>",
        "Translation:": "🇷🇺 <b>Translation:</b>",
        "Context:": "📃 <b>Context:</b>",
        "Example:": "📝 <b>Example:</b>"
    }
    for key, val in replacements.items():
        content = content.replace(key, val)
        
    return content

# --- ГЕНЕРАЦИЯ ---
def try_generate_once(current_topic):
    prompt = f"""
    Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2).
    ТЕМА: {current_topic}.
    Фраза НЕ должна быть банальной.
    
    Вся описательная часть СТРОГО на РУССКОМ. Используй HTML.
    Формат ответа строго такой:

    Phrase: [Сама фраза]
    Transcription: <i>[Транскрипция русскими буквами]</i>
    Translation: [Перевод]
    Context: <i>[Описание ситуации на русском]</i>
    Example:
    <blockquote>
    — [Диалог] (перевод)
    — [Диалог] (перевод)
    </blockquote>
    """

    for model in MODELS:
        try:
            print(f"   ⏳ Запрос к {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_SECONDS,
                extra_headers={"HTTP-Referer": "https://github.com"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"   ❌ Ошибка модели {model}: {e}")
            time.sleep(1)
    return None

def generate_unique_phrase():
    used_phrases = load_history()
    
    # Делаем 3 попытки найти уникальную фразу
    for attempt in range(3):
        topic = random.choice(TOPICS)
        print(f"🎲 Попытка {attempt+1}. Тема: {topic}")
        
        raw_content = try_generate_once(topic)
        
        if not raw_content:
            continue

        # Форматируем
        final_text = format_content(raw_content)
        
        # Проверяем на дубликаты
        is_duplicate = False
        for used in used_phrases:
            if len(used) > 5 and used in final_text.lower():
                print(f"♻️ ДУБЛИКАТ! Фраза '{used}' уже была.")
                is_duplicate = True
                break
        
        if not is_duplicate:
            return final_text

    print("💀 Не удалось сгенерировать уникальную фразу.")
    return None

def send_telegram_message(text):
    print("--- [3] Отправляю сообщение в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ Отправлено!")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

if __name__ == "__main__":
    phrase = generate_unique_phrase()
    if phrase:
        send_telegram_message(phrase)
        save_to_history(phrase)
    else:
        print("Остановка.")
