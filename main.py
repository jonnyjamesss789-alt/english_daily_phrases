import os
import requests
from openai import OpenAI
import time
import random
import re

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 120 # DeepSeek R1 может "думать" долго, даем ему время
HISTORY_FILE = "history.txt"

# ТВОЯ МОДЕЛЬ
# Я поставил стандартный алиас для DeepSeek R1 на OpenRouter.
# Если твой специфический ID "deepseek/deepseek-r1-0528-qwen3-8b" не сработает,
# код автоматически попробует официальный "deepseek/deepseek-r1".
MODEL_NAME = "deepseek/deepseek-r1" 

# СПИСОК ТЕМ (Для разнообразия)
TOPICS = [
    "Travel & Airports", "Business & Negotiations", "Love & Romance", 
    "Food & Cooking", "Friendship & Socializing", "Conflict Resolution", 
    "Money & Finance", "Health & Medicine", "Time Management", 
    "Weather & Climate", "Slang & Gen Z", "Idioms & Proverbs", 
    "Hobbies & Fitness", "Technology & AI", "Family Relationships", 
    "Driving & Cars", "University & Education", "Household Chores", 
    "Emotions & Psychology", "Politeness & Etiquette", "Job Interview", 
    "Movies & TV Shows", "Shopping & Fashion", "Real Estate & Home"
]

print("--- [1] START (PAID MODE) ---")

# --- КЛЮЧИ ---
def get_key(name):
    val = os.environ.get(name)
    if val: return str(val).strip()
    return None

BOT_TOKEN = get_key("BOT_TOKEN")
CHANNEL_ID = get_key("CHANNEL_ID")
OPENROUTER_API_KEY = get_key("OPENROUTER_API_KEY")

if not BOT_TOKEN or not CHANNEL_ID or not OPENROUTER_API_KEY:
    print("❌ KEYS MISSING! Check GitHub Secrets.")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- ИСТОРИЯ (Чтобы не было повторов) ---
def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f.readlines()]
    except: return []

def save_to_history(text):
    try:
        # Пытаемся вытащить саму фразу для сохранения
        if "Phrase:" in text:
            p = text.split("Phrase:")[1]
            clean = p.split("Transcription:")[0].strip()
            # Чистим от HTML тегов и эмодзи
            clean = re.sub(r'<[^>]+>', '', clean) 
            clean = clean.replace("🇺🇸", "").strip()
            
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(clean + "\n")
            print(f"💾 Saved to history: {clean}")
    except Exception as e:
        print(f"⚠️ History save error: {e}")

# --- ОЧИСТКА ОТ "МЫСЛЕЙ" DEEPSEEK ---
def clean_deepseek_thoughts(text):
    # DeepSeek R1 часто пишет <think>...</think>. Удаляем это.
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()

# --- ФОРМАТИРОВАНИЕ ---
def format_final_message(text):
    # 1. Удаляем Markdown блоки и мысли
    text = clean_deepseek_thoughts(text)
    text = text.replace("```html", "").replace("```", "").strip()
    
    # 2. Гарантированно расставляем твои смайлы и теги
    # Сначала сносим старые заголовки, чтобы не дублировались
    lines = text.split('\n')
    new_lines = []
    
    # Словарик замен
    replacements = {
        "Phrase:": "🇺🇸 <b>Phrase:</b>",
        "Transcription:": "🔊 <b>Transcription:</b>",
        "Translation:": "🇷🇺 <b>Translation:</b>",
        "Context:": "📃 <b>Context:</b>",
        "Example:": "📝 <b>Example:</b>"
    }

    # Проходим по тексту и заменяем заголовки
    for line in lines:
        for plain, fancy in replacements.items():
            if plain in line and "<b>" not in line: # Если еще не отформатировано
                line = line.replace(plain, fancy)
        new_lines.append(line)
        
    return "\n".join(new_lines)

# --- ГЕНЕРАЦИЯ ---
def generate_phrase():
    history = load_history()
    
    # Делаем 3 попытки (на случай, если попадется дубликат)
    for i in range(3):
        topic = random.choice(TOPICS)
        print(f"🎲 Topic: {topic}")
        
        prompt = f"""
        Generate ONE useful, natural English phrase (level B1-B2) about: {topic}.
        Output strictly in the format below. 
        NO markdown code blocks. NO introductory text.
        
        Format requirements:
        1. Transcription must be in RUSSIAN letters (Cyrillic transliteration).
        2. Context/Description must be in RUSSIAN.
        3. Use HTML tags <b>, <i>, <blockquote>.
        
        Template:
        Phrase: [English phrase]
        Transcription: <i>[Russian transcription, e.g. хау а ю]</i>
        Translation: [Russian translation]
        Context: <i>[Explanation in Russian]</i>
        Example:
        <blockquote>
        — [Dialog line 1]
        — [Dialog line 2]
        </blockquote>
        """

        try:
            print(f"⏳ Asking {MODEL_NAME}...")
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                timeout=TIMEOUT_SECONDS,
                extra_headers={"HTTP-Referer": "https://github.com"}
            )
            
            content = response.choices[0].message.content
            if not content: continue

            # Чистим и форматируем
            final_text = format_final_message(content)
            
            # Проверка на дубликаты
            is_dup = False
            for h in history:
                if len(h) > 5 and h in final_text.lower():
                    print(f"♻️ Duplicate found: {h}")
                    is_dup = True
                    break
            
            if not is_dup:
                return final_text # Ура, уникальная фраза!

        except Exception as e:
            print(f"❌ API Error: {e}")
            time.sleep(2)
            
    return None

# --- ОТПРАВКА ---
def send_telegram(text):
    print("--- Sending to Telegram ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    
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
        send_telegram(phrase)
        save_to_history(phrase)
    else:
        print("💀 Failed to generate phrase after attempts.")
