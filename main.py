import os
import requests
from openai import OpenAI
import time

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 60

# Список моделей
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "huggingfaceh4/zephyr-7b-beta:free"
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

def format_message(content):
    """
    Эта функция принудительно расставляет смайлы и теги,
    даже если нейросеть их забыла.
    """
    # 1. Убираем лишние Markdown символы, если они есть
    content = content.replace("**", "").replace("###", "").strip()
    
    # 2. Принудительная замена заголовков на красивые
    # Мы ищем просто слово "Phrase:" и меняем его на "🇬🇧 <b>Phrase:</b>"
    replacements = {
        "Phrase:": "🇬🇧 <b>Phrase:</b>",
        "Transcription:": "🔊 <b>Transcription:</b>",
        "Translation:": "🇷🇺 <b>Translation:</b>",
        "Context:": "💡 <i>Context:</i>",
        "Example:": "💎 <b>Example:</b>"
    }
    
    for old, new in replacements.items():
        # Заменяем и с двоеточием, и без (на всякий случай)
        content = content.replace(old, new)
        content = content.replace(old.replace(":", ""), new)

    # 3. Добавляем цитату для примера (если её нет)
    if "<blockquote>" not in content and "💎 <b>Example:</b>" in content:
        # Ищем, где начинается пример, и оборачиваем всё, что после него
        parts = content.split("💎 <b>Example:</b>")
        if len(parts) > 1:
            main_part = parts[0]
            example_part = parts[1].strip()
            # Собираем заново с тегом blockquote
            content = f"{main_part}💎 <b>Example:</b>\n<blockquote>{example_part}</blockquote>"

    return content

def generate_phrase():
    # Просим нейросеть дать ПРОСТОЙ текст, без оформления.
    # Оформление мы наложим сами в функции format_message.
    prompt = """
Generate one useful English phrase (B1-B2 level).
OUTPUT PLAIN TEXT ONLY. NO MARKDOWN. NO HTML.

Format strictly:
Phrase: [English phrase]
Transcription: [Russian letters transcription, e.g. хау а ю]
Translation: [Russian translation]
Context: [Russian explanation in 1 sentence]
Example:
- [Dialog line 1]
- [Dialog line 2]
- (Translation)
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
            
            raw_content = response.choices[0].message.content
            # ТУТ МАГИЯ: Применяем наше форматирование
            formatted_content = format_message(raw_content)
            
            return formatted_content
            
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
