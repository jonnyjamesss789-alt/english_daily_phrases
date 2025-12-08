import os
import requests
from openai import OpenAI
import time
import random

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50

# СПИСОК МОДЕЛЕЙ
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "google/gemini-2.0-flash-exp:free"
]

# СПИСОК ТЕМ (Чтобы фразы не повторялись)
TOPICS = [
    "Travel & Airports (Путешествия)", "Business & Office (Работа)", 
    "Emotions & Feelings (Чувства)", "Food & Restaurants (Еда)",
    "Friendship (Дружба)", "Conflict & Arguments (Споры)",
    "Money & Shopping (Деньги)", "Health & Body (Здоровье)",
    "Time & Planning (Время)", "Weather (Погода)",
    "Slang & Informal (Сленг)", "Idioms (Идиомы)",
    "Hobbies & Sports (Хобби)", "Technology (Технологии)",
    "Dating & Relationships (Отношения)", "Driving & Cars (Вождение)",
    "Education (Учеба)", "Household Chores (Домашние дела)",
    "Surprise & Shock (Удивление)", "Agreement & Disagreement (Согласие)",
    "Apologies (Извинения)", "Gratitude (Благодарность)",
    "Phone Calls (Телефон)", "Social Media (Соцсети)",
    "Movies & Books (Развлечения)", "Job Interview (Собеседование)",
    "Success & Failure (Успех и провал)", "Description of people (Описание людей)",
    "Cities & Directions (Ориентация в городе)", "Politeness (Вежливость)"
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
    print("❌ ОШИБКА: Отсутствуют ключи в Secrets!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    # 1. Выбираем случайную тему
    current_topic = random.choice(TOPICS)
    print(f"🎲 Выбрана тема: {current_topic}")

    # 2. Вставляем тему в промпт
    prompt = f"""
    Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2).
    ТЕМА ФРАЗЫ: {current_topic}. Фраза должна быть не банальной.
    
    Вся описательная часть должна быть СТРОГО на РУССКОМ языке.
    Используй HTML-теги. Обязательно делай отступы между блоками.
    Формат ответа строго такой:

    Phrase: [Сама фраза]

    Transcription: <i>[Правильная транскрипция с транслитерацией русскими буквами.]</i>

    Translation: [Перевод фразы]

    Context: <i>[Объяснение на русском в 1-2 предложениях, когда это используется]</i>

    Example:
    <blockquote>
    — [Пример диалога на английском] (в скобках перевод)
    — [Продолжение диалога] (в скобках перевод)
    </blockquote>
    """
    
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
            content = content.replace("```html", "").replace("```", "").strip()

            # --- ПРИНУДИТЕЛЬНАЯ РАССТАНОВКА СМАЙЛОВ ---
            
            # Очистка
            replacements_clean = {
                "<b>Phrase:</b>": "Phrase:", "<b>Transcription:</b>": "Transcription:",
                "<b>Translation:</b>": "Translation:", "<b>Context:</b>": "Context:",
                "<b>Example:</b>": "Example:"
            }
            for old, new in replacements_clean.items():
                content = content.replace(old, new)

            # Ваши смайлы: 🇺🇸, 🔊, 🇷🇺, 📃, 📝
            final_replacements = {
                "Phrase:": "🇺🇸 <b>Phrase:</b>",
                "Transcription:": "🔊 <b>Transcription:</b>",
                "Translation:": "🇷🇺 <b>Translation:</b>",
                "Context:": "📃 <b>Context:</b>",
                "Example:": "📝 <b>Example:</b>"
            }
            
            for key, val in final_replacements.items():
                content = content.replace(key, val)

            return content
            
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
