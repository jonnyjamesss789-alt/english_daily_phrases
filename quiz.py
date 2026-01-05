import os
import random
import json
import requests
import re
from openai import OpenAI

# --- НАСТРОЙКИ ---
HISTORY_FILE = "history.txt"
TIMEOUT_SECONDS = 60
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
            raw_lines = f.readlines()
            
        valid_phrases = []
        
        # --- УМНАЯ ФИЛЬТРАЦИЯ ---
        for line in raw_lines:
            line = line.strip()
            
            # 1. Если строка пустая - пропускаем
            if not line:
                continue
                
            # 2. Если в строке НЕТ английских букв (только смайлы или цифры) - пропускаем
            if not re.search(r'[a-zA-Z]', line):
                continue
            
            # 3. Чистим строку от мусора
            clean = line.replace("🇺🇸", "").replace("🇬🇧", "").replace("Phrase:", "")
            # Удаляем всё в начале, пока не встретим букву (чтобы убрать смайлы перед текстом)
            clean = re.sub(r'^[^a-zA-Z]+', '', clean).strip()
            
            # 4. Если после чистки что-то осталось (длиннее 2 букв), добавляем в список
            if len(clean) > 2:
                valid_phrases.append(clean)
        
        if not valid_phrases:
            print("⚠️ No valid phrases found in history.")
            return None
            
        # Выбираем случайную из УЖЕ очищенных
        return random.choice(valid_phrases)
        
    except Exception as e:
        print(f"❌ Error loading history: {e}")
        return None

def generate_quiz_data(phrase):
    print(f"🎲 Generating quiz for: {phrase}")
    
    prompt = f"""
    I have an English phrase: "{phrase}".
    Create a challenging Russian translation quiz for it.
    
    CRITICAL INSTRUCTIONS FOR WRONG ANSWERS:
    1. Must be grammatically CORRECT Russian sentences. NO TYPOS.
    2. Must have a DIFFERENT meaning (traps, false friends, literal translations).
    3. Do NOT use nonsense. Make the user THINK.
    
    Output STRICTLY in JSON:
    {{
        "correct": "Correct translation",
        "wrong1": "Trap translation 1",
        "wrong2": "Trap translation 2"
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
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        return None

def send_telegram_poll(phrase, quiz_data):
    print("--- Sending Quiz ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    
    options = [
        quiz_data["correct"],
        quiz_data["wrong1"],
        quiz_data["wrong2"]
    ]
    random.shuffle(options)
    correct_id = options.index(quiz_data["correct"])
    
    # --- ОФОРМЛЕНИЕ ВОПРОСА ---
    # Добавлены явные переносы строк (\n\n)
    question_text = f"🎯 Проверь себя!\n\n🇬🇧 {phrase}\n\n👇 Выбери верный перевод:"
    
    if len(question_text) > 295:
        question_text = f"🇬🇧 {phrase}\n\n👇 Перевод:"

    explanation_text = f"✅ Верно!\n\n🇬🇧 {phrase}\n🇷🇺 {quiz_data['correct']}"

    payload = {
        "chat_id": CHANNEL_ID,
        "question": question_text,
        "options": json.dumps(options),
        "is_anonymous": True,
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
        print(f"Selected phrase: {phrase}")
        data = generate_quiz_data(phrase)
        if data:
            send_telegram_poll(phrase, data)
    else:
        print("⚠️ No valid phrase could be loaded.")
