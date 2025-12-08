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
    "google/gemini-2.0-flash-exp:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

# СПИСОК ТЕМ
TOPICS = [
    "Travel", "Business", "Emotions", "Food", "Friendship", "Conflict", 
    "Money", "Health", "Time", "Weather", "Slang", "Idioms", "Hobbies", 
    "Technology", "Relationships", "Driving", "Education", "Household", 
    "Surprise", "Agreement", "Politeness", "Job Interview", "Movies"
]

print("--- [1] START ---")

def get_env_key(key_name):
    value = os.environ.get(key_name)
    if value:
        return str(value).strip()
    return None

BOT_TOKEN = get_env_key("BOT_TOKEN")
CHANNEL_ID = get_env_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_env_key("OPENROUTER_API_KEY")

if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ KEYS MISSING!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- ИСТОРИЯ ---
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f.readlines()]
    except:
        return []

def save_to_history(text):
    # Простое сохранение без лишних проверок
    try:
        if "Phrase:" in text:
            part = text.split("Phrase:")[1]
            # Берем кусок до транскрипции
            clean = part.split("Transcription:")[0].strip()
            # Убираем возможные теги
            clean = clean.replace("<b>", "").replace("</b>", "")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(clean + "\n")
            print(f"💾 Saved: {clean}")
    except Exception as e:
        print(f"⚠️ Save error: {e}")

# --- ГЕНЕРАЦИЯ ---
def get_prompt(topic):
    return f"""
Generate one useful English phrase (B1-B2 level).
TOPIC: {topic}.
Do not use Markdown blocks (no ```).
Use HTML tags strictly.

Format:
Phrase: [Phrase]
Transcription: <i>[Russian transcription]</i>
Translation: [Russian translation]
Context: <i>[Russian context]</i>
Example:
<blockquote>
- [Dialog]
- [Dialog]
</blockquote>
"""

def generate_phrase():
    history = load_history()
    
    for attempt in range(3):
        topic = random.choice(TOPICS)
        print(f"🎲 Topic: {topic}")
        
        prompt = get_prompt(topic)
        
        for model in MODELS:
            try:
                print(f"   ⏳ Asking {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=TIMEOUT_SECONDS,
                    extra_headers={"HTTP-Referer": "[https://github.com](https://github.com)"}
                )
                content = response.choices[0].message.content
                content = content.replace("```html", "").replace("```", "").strip()
                
                # --- ФОРМАТИРОВАНИЕ ---
                # Очистка от старых тегов
                content = content.replace("<b>Phrase:</b>", "Phrase:")
                content = content.replace("<b>Transcription:</b>", "Transcription:")
                content = content.replace("<b>Translation:</b>", "Translation:")
                content = content.replace("<b>Context:</b>", "Context:")
                content = content.replace("<b>Example:</b>", "Example:")
                
                # Добавление красивых тегов и смайлов
                content = content.replace("Phrase:", "🇺🇸 <b>Phrase:</b>")
                content = content.replace("Transcription:", "🔊 <b>Transcription:</b>")
                content = content.replace("Translation:", "🇷🇺 <b>Translation:</b>")
                content = content.replace("Context:", "📃 <b>Context:</b>")
                content = content.replace("Example:", "📝 <b>Example:</b>")
                
                # Проверка на дубликаты
                is_duplicate = False
                for h in history:
                    if len(h) > 5 and h in content.lower():
                        print(f"♻️ Duplicate found: {h}")
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    break # Пробуем другую тему (attempt)
                
                return content # Успех!

            except Exception as e:
                print(f"   ❌ Error {model}: {e}")
                time.sleep(1)
                
    return None

def send_telegram(text):
    print("--- Sending to Telegram ---")
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print("✅ Sent!")
        else:
            print(f"❌ Telegram Error: {resp.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    phrase = generate_phrase()
    if phrase:
        send_telegram(phrase)
        save_to_history(phrase)
    else:
        print("💀 Failed to generate.")
