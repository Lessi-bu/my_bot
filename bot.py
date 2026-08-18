from flask import Flask, request
import os
import logging

app = Flask(__name__)

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')

@app.route('/')
def index():
    """Главная страница - проверка, что бот жив"""
    return "Бот работает! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Сюда Telegram будет присылать сообщения"""
    try:
        # Получаем данные от Telegram
        data = request.get_json()
        
        # Проверяем, что это сообщение от пользователя
        if 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')
            
            # Если пользователь написал /start
            if text == '/start':
                send_message(chat_id, "👋 Привет! Я простой бот, который работает!")
            else:
                send_message(chat_id, f"Вы написали: {text}")
        
        return "OK", 200
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return "Error", 500

def send_message(chat_id, text):
    """Отправляет сообщение пользователю"""
    import requests
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text
    }
    requests.post(url, json=data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)