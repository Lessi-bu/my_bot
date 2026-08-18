from flask import Flask, request
import os
import logging
import requests
import uuid
from googletrans import Translator

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Токен Telegram
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Создаём переводчик
translator = Translator()

@app.route('/')
def index():
    return "Бот работает! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')

            if text == '/start':
                send_message(chat_id,
                    "👋 Привет! Я бот для генерации картинок!\n\n"
                    "Просто напиши мне описание картинки на РУССКОМ языке, и я её нарисую!\n"
                    "🎨 Каждый день у тебя есть 1 бесплатная генерация!\n\n"
                    "Команды:\n"
                    "/start - приветствие\n"
                    "/help - помощь\n"
                    "/balance - сколько генераций осталось"
                )
            elif text == '/help':
                send_message(chat_id,
                    "🤖 Как пользоваться:\n"
                    "1. Напиши мне описание картинки на РУССКОМ языке\n"
                    "2. Я переведу запрос на английский и сгенерирую картинку\n\n"
                    "📊 У тебя есть 1 бесплатная генерация в день."
                )
            elif text == '/balance':
                send_message(chat_id,
                    "🎨 Сегодня у вас есть 1 бесплатная генерация!\n"
                    "Купленных генераций: 0\n\n"
                    "💡 Скоро появится возможность купить ещё!"
                )
            else:
                send_message(chat_id, "🎨 Рисую картинку... Подождите немного!")
                
                try:
                    # --- ПЕРЕВОД НА АНГЛИЙСКИЙ ---
                    try:
                        translation = translator.translate(text, dest='en')
                        prompt_en = translation.text
                        logging.info(f"Оригинал: {text} -> Перевод: {prompt_en}")
                    except Exception as e:
                        # Если перевод не сработал, используем оригинал
                        logging.warning(f"Перевод не сработал: {e}")
                        prompt_en = text
                    
                    # Генерируем картинку с переведённым запросом
                    unique_id = str(uuid.uuid4())
                    image_url = f"https://image.pollinations.ai/prompt/{prompt_en.replace(' ', '%20')}?n={unique_id}&width=1024&height=1024"
                    
                    # Скачиваем картинку
                    response = requests.get(image_url, timeout=60)
                    
                    if response.status_code == 200:
                        # Отправляем картинку с обоими запросами (русским и английским)
                        caption = f"🎨 Ваш запрос: {text}\n🌍 Перевод: {prompt_en}"
                        send_photo(chat_id, response.content, caption)
                    else:
                        send_message(chat_id, f"❌ Ошибка от сервера: {response.status_code}")
                        
                except Exception as e:
                    send_message(chat_id, f"❌ Ошибка: {str(e)}")

        return "OK", 200
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return "Error", 500

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass

def send_photo(chat_id, image_data, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('image.png', image_data, 'image/png')}
    data = {'chat_id': chat_id, 'caption': caption}
    try:
        requests.post(url, data=data, files=files, timeout=30)
    except Exception as e:
        send_message(chat_id, f"❌ Не удалось отправить картинку: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
