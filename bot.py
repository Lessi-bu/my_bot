from flask import Flask, request
import os
import logging
import requests
import base64
from io import BytesIO

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 1. Получаем наши токены из переменных окружения Render
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
HF_API_TOKEN = os.environ.get('HF_API_TOKEN') # <-- Токен от Hugging Face

# 2. Конфигурация модели Hugging Face
# Используем популярную и стабильную модель Stable Diffusion
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

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
                    "📊 У тебя есть 1 бесплатная генерация в день."
                )
            elif text == '/balance':
                send_message(chat_id,
                    "🎨 Сегодня у вас есть 1 бесплатная генерация!\n"
                    "Купленных генераций: 0\n\n"
                    "💡 Скоро появится возможность купить ещё!"
                )
            else:
                # --- Генерация изображения через Hugging Face ---
                send_message(chat_id, "🎨 Рисую картинку... Подождите немного!")

                # Функция для запроса к API
                def query(payload):
                    response = requests.post(API_URL, headers=headers, json=payload)
                    return response.content

                try:
                    # Отправляем запрос в Hugging Face
                    image_bytes = query({
                        "inputs": text,  # Ваш запрос от пользователя
                    })

                    # Проверяем, не пришла ли ошибка в виде JSON
                    if image_bytes.startswith(b'{') and b'error' in image_bytes:
                        error_msg = image_bytes.decode('utf-8')
                        send_message(chat_id, f"❌ Ошибка от сервера: {error_msg}")
                    else:
                        # Отправляем картинку обратно пользователю
                        send_photo(chat_id, image_bytes, f"Вот что я нарисовал по запросу: {text}")

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
