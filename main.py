import os
import requests
from openai import OpenAI
import time

# --- НАСТРОЙКИ ---
TIMEOUT_SECONDS = 50

# СПИСОК МОДЕЛЕЙ (Оставляем рабочие)
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
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

def generate_phrase():
    # ОБНОВЛЕННЫЙ ПРОМПТ
    # Добавил требование писать транскрипцию КИРИЛЛИЦЕЙ
    prompt = (
        "Сгенерируй одну полезную разговорную фразу на английском языке (уровень B1-B2). "
        "Вся описательная часть должна быть СТРОГО на РУССКОМ языке. "
        "Используй HTML-теги. "
        "ВАЖНО: Транскрипция должна быть написана РУССКИМИ БУКВАМИ (кириллицей), передавая примерное звучание (например: 'ай лав ю').\n"
        "Обязательно делай двойные отступы между блоками. "
        "Формат ответа строго такой:\n\n"
        
        "🇬🇧 Phrase: <b>[Сама фраза жирным]</b>\n\n"
        
        "🔊 Transcription: <code>[Транскрипция русскими буквами]</code>\n\n"
        
        "🇷🇺 Translation: [Перевод фразы]\n\n"
        
        "💡 <i>Context: [Объяснение на русском в 1-2 предложениях]</i>\n\n"
        
        "💎 Example:\n"
        "<blockquote>"
        "— [Пример диалога на английском]\n"
        "— [Продолжение диалога]\n"
        "— (Перевод в скобках)"
        "</blockquote>"
    )
    
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
            
            content = response.choices[0].message.content
            content = content.replace("```html", "").replace("```", "").strip()
            return content
            
        except
