import os
import requests
from openai import OpenAI
import time
import random

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50
HISTORY_FILE = "history.txt"

# МОДЕЛИ
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

# ТЕМЫ
TOPICS = [
    "Travel", "Business", "Emotions", "Food", "Friendship", "Conflict", 
    "Money", "Health", "Time", "Weather", "Slang", "Idioms", "Hobbies", 
    "Technology", "Relationships", "Driving", "Education", "Household", 
    "Surprise", "Agreement", "Politeness", "Job Interview", "Movies"
]

print("--- START ---")

# --- КЛЮЧИ ---
def get_key(name):
    val = os.environ.get(name)
    if val:
        return str(val).strip()
    return None

BOT_TOKEN = get_key("BOT_TOKEN")
CHANNEL_ID = get_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_key("OPENROUTER_API_KEY")

if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ KEYS MISSING")
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
    try:
        if "Phrase:" in text:
            # Вырезаем фразу для сохранения
            p = text.split("Phrase:")[1]
            clean = p.split("Transcription:")[0].strip()
            # Убираем HTML теги
            clean = clean.replace("<b>", "").replace("</b>", "")
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(clean + "\n")
            print(f"💾 Saved: {clean}")
    except Exception as e:
        print(f"⚠️ Save Error: {e}")

# --- ФОРМАТИРОВАНИЕ ---
def format_text(text):
    text = text.replace("```html", "").replace("```", "").strip()
    
    # 1. Сначала убираем старые теги, если нейросеть их добавила
    clean_pairs = {
        "<b>Phrase:</b>": "Phrase:", "<b>Transcription:</b>": "Transcription:",
        "<b>Translation:</b>": "Translation:", "<b>Context:</b>": "Context:", 
        "<b>Example:</b>": "Example:"
    }
    for k, v in clean_pairs.items():
        text = text.replace(k, v)

    # 2. Ставим новые красивые теги и смайлы
    emoji_pairs = {
        "Phrase:": "🇺🇸 <b>Phrase:</b>",
        "Transcription:": "🔊 <b>Transcription:</b>",
        "Translation:": "🇷🇺 <b>Translation:</b>",
        "Context:": "📃 <b>Context:</b>",
        "Example:": "📝 <b>Example:</b>"
    }
    for k, v in emoji_pairs.items():
        text = text.replace(k, v)
        
    return text

# --- ГЕНЕРАЦИЯ ---
def ask_ai(topic):
    prompt = f"""
Generate one useful English phrase (B1-B2 level).
TOPIC: {topic}.
Do not use Markdown blocks. Use HTML tags.

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
    for model in MODELS:
        try:
            print(f"⏳ Asking {model}...")
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_SECONDS,
                extra_headers={"HTTP-Referer": "https://github.com"}
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"❌ Error {model}: {e}")
            time.sleep(1)
    return None

def main_loop():
    history = load_history()
    
    # 3 попытки найти уникальную фразу
    for i in range(3):
        topic = random.choice(TOPICS)
        print(f"🎲 Topic: {topic}")
        
        raw_text = ask_ai(topic)
        if not raw_text:
            continue
            
        final_text = format_text(raw_text)
        
        # Проверка на дубликаты
        is_dup = False
        for h in history:
            if len(h) > 5 and h in final_text.lower():
                print(f"♻️ Duplicate: {h}")
                is_dup = True
                break
        
        if not is_dup:
            return final_text
            
    return None

# --- ОТПРАВКА ---
def send_telegram(text):
    print("--- Sending ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ Sent!")
    except Exception as e:
        print(f"❌ Send Error: {e}")

if __name__ == "__main__":
    result = main_loop()
    if result:
        send_telegram(result)
        save_to_history(result)
    else:
        print("💀 Failed to generate unique phrase")
