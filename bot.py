from flask import Flask, request
import os
import logging
import requests
import google.generativeai as genai

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Токены
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')

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
                    "Просто напиши мне описание картинки, и я её нарисую!\n"
                    "🎨 Каждый день у тебя есть 1 бесплатная генерация!\n\n"
                    "Команды:\n"
                    "/start - приветствие\n"
                    "/help - помощь\n"
                    "/balance - сколько генераций осталось"
                )
            elif text == '/help':
                send_message(chat_id,
                    "🤖 Как пользоваться:\n"
                    "1. Напиши мне описание картинки\n"
                    "2. Я сгенерирую её для тебя\n\n"
                    "📊 У тебя есть 1 бесплатная генерация в день.\n"
                    "💰 Дополнительные генерации можно будет купить позже."
                )
            elif text == '/balance':
                send_message(chat_id,
                    "🎨 Сегодня у вас есть 1 бесплатная генерация!\n"
                    "Купленных генераций: 0\n\n"
                    "💡 Скоро появится возможность купить ещё!"
                )
            else:
                # Генерация картинки
                send_message(chat_id, "🎨 Рисую картинку... Подождите немного!")
                try:
                    response = model.generate_content(
                        f"Нарисуй: {text}",
                        generation_config={"response_modalities": ["IMAGE"]}
                    )
                    # Получаем ссылку на картинку
                    image_url = response.candidates[0].content.parts[0].inline_data.data
                    import base64
                    image_data = base64.b64decode(image_url)
                    
                    # Отправляем картинку
                    send_photo(chat_id, image_data, f"Вот что я нарисовал по запросу: {text}")
                except Exception as e:
                    send_message(chat_id, f"❌ Ошибка при генерации: {str(e)}")
        
        return "OK", 200
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return "Error", 500

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=data)

def send_photo(chat_id, image_data, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('image.png', image_data, 'image/png')}
    data = {'chat_id': chat_id, 'caption': caption}
    requests.post(url, data=data, files=files)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
