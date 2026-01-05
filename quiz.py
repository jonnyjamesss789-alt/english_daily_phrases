import os
import random
import json
import requests
import re
from openai import OpenAI

# --- НАСТРОЙКИ ---
HISTORY_FILE = "history.txt"
TIMEOUT_SECONDS = 60

# --- КЛЮЧИ ---
def get_key(name):
    val = os.environ.get(name)
    if val: return str(val).strip()
    return None

BOT_TOKEN = get_key("BOT_TOKEN")
CHANNEL_ID = get_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_key("OPENROUTER_API_KEY")

if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ KEYS MISSING!")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def load_random_phrase():
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines:
            return None
        return random.choice(lines)
    except:
        return None

def generate_quiz_data(phrase):
    print(f"🎲 Generating quiz for: {phrase}")
    
    # Просим DeepSeek вернуть строго JSON
    prompt = f"""
    I have an English phrase: "{phrase}".
    Create a Russian translation quiz for it.
    
    Task:
    1. Provide the correct Russian translation.
    2. Provide 2 INCORRECT but plausible Russian translations (distractors).
    3. Output strictly in JSON format.
    
    JSON Structure:
    {{
        "correct": "Правильный перевод",
        "wrong1": "Неправильный перевод 1",
        "wrong2": "Неправильный перевод 2"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=TIMEOUT_SECONDS,
            extra_headers={"HTTP-Referer": "https://github.com"}
        )
        
        content = response.choices[0].message.content
        
        # Чистим от <think> и markdown
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Парсим JSON
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        return None

def send_telegram_poll(phrase, quiz_data):
    print("--- Sending Quiz ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    
    # Формируем список вариантов
    options = [
        quiz_data["correct"],
        quiz_data["wrong1"],
        quiz_data["wrong2"]
    ]
    # Перемешиваем варианты, чтобы правильный не всегда был первым
    random.shuffle(options)
    
    # Находим индекс правильного ответа после перемешивания
    correct_id = options.index(quiz_data["correct"])
    
    payload = {
        "chat_id": CHANNEL_ID,
        "question": f"🇬🇧 Как переводится: {phrase}?",
        "options": json.dumps(options),
        "is_anonymous": True, # <--- ИСПРАВЛЕНО: Для каналов обязательно True
        "type": "quiz", # Режим викторины
        "correct_option_id": correct_id,
        "explanation": f"Correct translation: {quiz_data['correct']}" # Подсказка после ответа
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Quiz sent!")
        else:
            print(f"❌ Telegram Error: {resp.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    phrase = load_random_phrase()
    if phrase:
        data = generate_quiz_data(phrase)
        if data:
            send_telegram_poll(phrase, data)
    else:
        print("⚠️ No history file found or it's empty.")
