import os
import random
import json
import requests
import re
from openai import OpenAI

# --- НАСТРОЙКИ ---
HISTORY_FILE = "history.txt"
TIMEOUT_SECONDS = 60

# ТВОЯ МОДЕЛЬ
# Переключили на GPT-4o Mini, как ты просил.
# Она отлично генерирует JSON и понимает нюансы языка.
MODEL_NAME = "openai/gpt-4o-mini"

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
    
    # Усиленный промпт для сложных вариантов
    prompt = f"""
    I have an English phrase: "{phrase}".
    Create a challenging Russian translation quiz for it.
    
    CRITICAL INSTRUCTIONS FOR WRONG ANSWERS (DISTRACTORS):
    1. They must be grammatically CORRECT Russian sentences. NO TYPOS.
    2. They must make sense but have a DIFFERENT meaning.
    3. Use "traps":
       - Literal translations of idioms (if applicable).
       - Words that look/sound similar (false friends).
       - Wrong context or opposite meaning.
    4. Do NOT use obvious nonsense or random words. Make the user THINK.
    
    Output STRICTLY in JSON format:
    {{
        "correct": "Correct Russian translation (short)",
        "wrong1": "Plausible but incorrect translation (trap 1)",
        "wrong2": "Plausible but incorrect translation (trap 2)"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            timeout=TIMEOUT_SECONDS,
            extra_headers={"HTTP-Referer": "https://github.com"}
        )
        
        content = response.choices[0].message.content
        
        # Чистка от возможного форматирования markdown
        content = content.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        return None

def send_telegram_poll(phrase, quiz_data):
    print("--- Sending Quiz ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    
    # 1. Варианты ответа
    options = [
        quiz_data["correct"],
        quiz_data["wrong1"],
        quiz_data["wrong2"]
    ]
    random.shuffle(options)
    correct_id = options.index(quiz_data["correct"])
    
    # 2. Оформление вопроса
    question_text = f"🎯 Проверь себя!\n\n🇬🇧 {phrase}\n\n👇 Выбери верный перевод:\n"
    
    # Если слишком длинно, сокращаем
    if len(question_text) > 295:
        question_text = f"🇬🇧 {phrase}\n\n👇 Перевод:"

    # 3. Объяснение
    explanation_text = f"✅ Верно!\n\n🇬🇧 {phrase}\n🇷🇺 {quiz_data['correct']}"

    payload = {
        "chat_id": CHANNEL_ID,
        "question": question_text,
        "options": json.dumps(options),
        "is_anonymous": True, # Обязательно True для каналов
        "type": "quiz",
        "correct_option_id": correct_id,
        "explanation": explanation_text
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Quiz sent successfully!")
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
