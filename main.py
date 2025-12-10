import os
import requests
from openai import OpenAI
import time
import random
import re

# --- CONFIGURATION ---
TIMEOUT_SECONDS = 120
HISTORY_FILE = "history.txt"

# YOUR MODEL
MODEL_NAME = "deepseek/deepseek-r1"

TOPICS = [
    "Travel", "Business", "Emotions", "Food", "Friendship", "Conflict",
    "Money", "Health", "Time", "Weather", "Slang", "Idioms", "Hobbies",
    "Technology", "Relationships", "Education", "Household",
    "Surprise", "Agreement", "Politeness", "Job Interview", "Movies"
]

print("--- [1] START (PAID MODE) ---")

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

# --- HISTORY ---
def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f.readlines()]
    except: return []

def save_to_history(text):
    try:
        if "Phrase:" in text:
            # Extract plain phrase
            p = text.split("Phrase:")[1]
            clean = p.split("Transcription:")[0].strip()
            # Remove HTML tags
            clean = re.sub(r'<[^>]+>', '', clean)
            clean = clean.replace("🇺🇸", "").strip()

            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(clean + "\n")
            print(f"💾 Saved history: {clean}")
    except Exception as e:
        print(f"⚠️ History error: {e}")

# --- CLEANING AND FORMATTING ---
def clean_and_format(text):
    # 1. Remove DeepSeek thoughts <think>...</think>
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # 2. Fix Telegram 400 Errors (The part that caused SyntaxError before is fixed here)
    # We simply replace specific bad tags with newlines
    text = text.replace("\\br\\", "\n")
    text = text.replace("<br>", "\n")
    text = text.replace("<br/>", "\n")
    text = text.replace("```html", "").replace("```", "").strip()

    # 3. Add Emojis and Bold tags if missing
    replacements = {
        "Phrase:": "🇺🇸 <b>Phrase:</b>",
        "Transcription:": "🔊 <b>Transcription:</b>",
        "Translation:": "🇷🇺 <b>Translation:</b>",
        "Context:": "📃 <b>Context:</b>",
        "Example:": "📝 <b>Example:</b>"
    }

    lines = text.split('\n')
    new_lines = []
    for line in lines:
        processed_line = line
        for plain, fancy in replacements.items():
            # Only replace if not already formatted
            if plain in processed_line and "<b>" not in processed_line:
                processed_line = processed_line.replace(plain, fancy)
        new_lines.append(processed_line)

    return "\n".join(new_lines)

# --- GENERATION ---
def generate_phrase():
    history = load_history()

    for i in range(3):
        topic = random.choice(TOPICS)
        print(f"🎲 Topic: {topic}")

        # Prompt explicitly asking for clean HTML
        prompt = f"""
        Generate ONE useful English phrase (level B1-B2) about: {topic}.
        Output strictly in the format below.
        NO markdown code blocks. NO introductory text.

        Format requirements:
        1. Transcription must be in RUSSIAN letters (Cyrillic).
        2. Context/Description must be in RUSSIAN.
        3. Use ONLY these HTML tags: <b>, <i>, <blockquote>. DO NOT use <br>.

        Template:
        Phrase: [English phrase]
        
        Transcription: <i>[Russian transcription]</i>
        
        Translation: [Russian translation]
        
        Context: <i>[Explanation in Russian]</i>
        
        Example:
        <blockquote>
        — <b>[Dialog line 1]</b> (перевод фразы на русский язык)
        — <b>[Dialog line 2]</b> (перевод фразы на русский язык)
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

            final_text = clean_and_format(content)

            # Check for duplicates
            is_dup = False
            for h in history:
                if len(h) > 5 and h in final_text.lower():
                    print(f"♻️ Duplicate: {h}")
                    is_dup = True
                    break

            if not is_dup:
                return final_text

        except Exception as e:
            print(f"❌ API Error: {e}")
            time.sleep(2)

    return None

# --- SENDING (WITH FALLBACK) ---
def send_telegram(text):
    print("--- Sending to Telegram ---")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # Attempt 1: HTML Mode
    data_html = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=data_html, timeout=10)
        if resp.status_code == 200:
            print("✅ SENT (HTML)!")
            return True
        else:
            print(f"⚠️ HTML failed ({resp.status_code}). Trying plain text...")
            print(f"Error details: {resp.text}")
    except:
        pass

    # Attempt 2: Plain Text Fallback (Guarantees delivery)
    plain_text = re.sub(r'<[^>]+>', '', text) # Remove all tags
    data_plain = {"chat_id": CHANNEL_ID, "text": plain_text}

    try:
        resp = requests.post(url, data=data_plain, timeout=10)
        if resp.status_code == 200:
            print("✅ SENT (PLAIN TEXT FALLBACK)!")
            return True
        else:
            print(f"❌ FINAL ERROR: {resp.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

    return False

if __name__ == "__main__":
    phrase = generate_phrase()
    if phrase:
        if send_telegram(phrase):
            save_to_history(phrase)
    else:
        print("💀 Failed to generate.")
