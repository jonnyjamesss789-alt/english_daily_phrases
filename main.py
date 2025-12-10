import os
import requests
from openai import OpenAI
import time
import random

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 60

# СПИСОК МОДЕЛЕЙ (Самые живучие + твой запрос на Qwen)
MODELS = [
    # Тот самый Qwen (версия 2.5, так как 3 еще нет в доступе)
    "qwen/qwen3-235b-a22b:free",
    
    # Mistral (Он у тебя сработал на скриншоте!)
    "mistralai/mistral-7b-instruct:free",
    
    # Надежная Llama
    "meta-llama/llama-3-8b-instruct:free",
    
    # Google (Запасной)
    "google/gemini-2.0-flash-exp:free"
]

# ТЕМЫ (Чтобы не было скучно)
TOPICS = [
    "Travel", "Business", "Emotions", "Food", "Friendship", "Conflict", 
    "Money", "Health", "Time", "Weather", "Slang", "Idioms", "Hobbies", 
    "Technology", "Relationships", "Education", "Household", 
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
    print("❌ KEYS MISSING")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def generate_phrase():
    topic = random.choice(TOPICS)
    print(f"🎲 Topic: {topic}")
    
    # Промпт
    prompt = (
        f"Generate one useful English phrase (B1-B2 level) about: {topic}. "
        "Strictly follow the format below. Use HTML tags. "
        "Description must be in RUSSIAN.\n\n"
        "Format:\n"
        "🇺🇸 <b>Phrase:</b> [Phrase]\n\n"
        "🔊 <b>Transcription:</b> <i>[Russian transcription]</i>\n\n"
        "🇷🇺 <b>Translation:</b> [Translation]\n\n"
        "📃 <b>Context:</b> <i>[Context in Russian]</i>\n\n"
        "📝 <b>Example:</b>\n"
        "<blockquote>\n"
        "— [Dialog line 1]\n"
        "— [Dialog line 2]\n"
        "</blockquote>"
    )
    
    for model in MODELS:
        print(f"--- Asking: {model} ...")
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_SECONDS,
                extra_headers={"HTTP-Referer": "https://github.com"}
            )
            elapsed = time.time() - start_time
            
            content = response.choices[0].message.content
            if not content: 
                print("⚠️ Empty response")
                continue
                
            # Чистим мусор
            content = content.replace("```html", "").replace("```", "").strip()
            
            print(f"✅ SUCCESS! {model} answered in {elapsed:.2f}s")
            
            # --- ВОТ ОНО: ВОЗВРАЩАЕМ РЕЗУЛЬТАТ ---
            return content 
            
        except Exception as e:
            print(f"❌ Error {model}: {e}")
            time.sleep(1)
            
    return None

def send_telegram(text):
    print("--- Sending to Telegram ---")
    
    # Страховка: если нейросеть забыла флаг, добавим его
    if not text.startswith("🇺🇸"):
        text = "🇺🇸 " + text
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print("✅ SENT SUCCESSFULLY!")
        else:
            print(f"❌ TELEGRAM ERROR: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    phrase = generate_phrase()
    
    if phrase:
        # Если фраза есть - отправляем
        send_telegram(phrase)
    else:
        # Если фразы нет - паникуем
        print("💀 ALL MODELS FAILED. Check logs above.")
