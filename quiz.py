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
    
    prompt = f"""
    I have an English phrase: "{phrase}".
    Create a Russian translation quiz for it.
    
    Task:
    1. Provide the correct Russian translation (keep it short, max 5-6 words).
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
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = content.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        return None

def send_telegram_poll(phrase, quiz_data):
    print("--- Sending Quiz ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    
    # 1. Формируем варианты ответа
    options = [
        quiz_data["correct"],
        quiz_data["wrong1"],
        quiz_data["wrong2"]
    ]
    random.shuffle(options)
    correct_id = options.index(quiz_data["correct"])
    
    # 2. Красивое оформление вопроса
    # Лимит Телеграм на вопрос - 300 символов.
    
    # Вариант красивый:
    question_text = f"🎯 Проверь себя!\n\n🇬🇧 {phrase}\n\n👇 Выбери верный перевод:"
    
    # Если фраза очень длинная, используем компактный вариант:
    if len(question_text) > 295:
        question_text = f"🇬🇧 {phrase}\n\n👇 Перевод:"

    # 3. Красивое объяснение (появляется после ответа)
    explanation_text = f"✅ Верно!\n\n🇬🇧 {phrase}\n🇷🇺 {quiz_data['correct']}"

    payload = {
        "chat_id": CHANNEL_ID,
        "question": question_text,
        "options": json.dumps(options),
        "is_anonymous": True, # ОБЯЗАТЕЛЬНО True для каналов
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
