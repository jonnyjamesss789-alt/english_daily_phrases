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
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        # Читаем фразы, убираем переносы строк и приводим к нижнему регистру
        return [line.strip().lower() for line in f.readlines()]

def save_to_history(phrase_text):
    # Извлекаем саму английскую фразу из HTML (грубо, но эффективно)
    # Ищем текст между 🇺🇸 <b>Phrase:</b> и 🔊
    try:
        start_marker = "🇺🇸 <b>Phrase:</b>"
        end_marker = "🔊"
        if start_marker in phrase_text and end_marker in phrase_text:
            clean_phrase = phrase_text.split(start_marker)[1].split(end_marker)[0].strip()
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(clean_phrase + "\n")
            print(f"💾 Фраза '{clean_phrase}' сохранена в историю.")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить в историю: {e}")

# --- ГЕНЕРАЦИЯ ---
def generate_unique_phrase():
    used_phrases = load_history()
    
    # Делаем до 3 попыток, если попадается дубликат
    for attempt in range(3):
        current_topic = random.choice(TOPICS)
        print(f"🎲 Попытка {attempt+1}. Тема: {current_topic}")

        prompt = f"""
        Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2).
        ТЕМА: {current_topic}.
        Фраза НЕ должна быть банальной (как "How are you").
        
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
                
                content = response.choices[0].message.content
                content = content.replace("```html", "").replace("```", "").strip()

                # Форматирование и Смайлы
                replacements = {
                    "Phrase:": "🇺🇸 <b>Phrase:</b>",
                    "Transcription:": "🔊 <b>Transcription:</b>",
                    "Translation:": "🇷🇺 <b>Translation:</b>",
                    "Context:": "📃 <b>Context:</b>",
                    "Example:": "📝 <b>Example:</b>"
                }
                # Сначала чистим от старых тегов, если они есть
                clean_content = content.replace("<b>Phrase:</b>", "Phrase:") 
                
                # Применяем красивые теги
                for key, val in replacements.items():
                    clean_content = clean_content.replace(key, val)

                # --- ПРОВЕРКА НА ДУБЛИКАТЫ ---
                # Пытаемся найти фразу внутри текста
                is_duplicate = False
                for used in used_phrases:
                    if used in clean_content.lower():
                        print(f"♻️ ДУБЛИКАТ! Фраза '{used}' уже была. Пробуем снова...")
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    break # Выходим из цикла моделей, идем на следующую попытку генерации (attempt)
                
                # Если не дубликат - возвращаем результат
                return clean_content

            except Exception as e:
                print(f"   ❌ Ошибка модели: {e}")
                time.sleep(1)
        
    print("💀 Не удалось сгенерировать уникальную фразу за 3 попытки.")
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
        save_to_history(phrase) # Сохраняем в файл
    else:
        print("Остановка.")
