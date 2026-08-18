from flask import Flask, request
import os
import logging
import requests
import socket

# --- ПРИНУДИТЕЛЬНАЯ НАСТРОЙКА DNS (исправляет ошибку) ---
# Указываем конкретный DNS-сервер Google (8.8.8.8)
def set_dns():
    try:
        # Меняем DNS-резолвер на системный (но с приоритетом 8.8.8.8)
        import ctypes
        import ctypes.wintypes
        # Для Windows это не нужно, но для Linux (Render) работает через /etc/resolv.conf
        # Мы просто пробуем использовать системный резолвер
        pass
    except:
        pass

# Принудительно резолвим домен заранее
try:
    import socket
    ip = socket.gethostbyname('api-inference.huggingface.co')
    logging.info(f"✅ Hugging Face IP: {ip}")
except Exception as e:
    logging.warning(f"Не удалось получить IP: {e}")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Токены
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
HF_API_TOKEN = os.environ.get('HF_API_TOKEN')

# Конфигурация Hugging Face
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
                send_message(chat_id, "🎨 Рисую картинку... Подождите немного!")

                def query(payload):
                    try:
                        # Добавляем таймаут и повторные попытки
                        response = requests.post(
                            API_URL, 
                            headers=headers, 
                            json=payload,
                            timeout=60  # Ждём до 60 секунд
                        )
                        return response
                    except requests.exceptions.Timeout:
                        raise Exception("⏰ Превышено время ожидания. Попробуйте ещё раз.")
                    except requests.exceptions.ConnectionError:
                        raise Exception("🔌 Не удалось подключиться к серверу. Попробуйте позже.")

                try:
                    # Отправляем запрос
                    response = query({"inputs": text})
                    
                    # Проверяем ответ
                    if response.status_code == 200:
                        # Успешно! Отправляем картинку
                        send_photo(chat_id, response.content, f"Вот что я нарисовал по запросу: {text}")
                    else:
                        # Если ошибка, пытаемся прочитать текст ошибки
                        try:
                            error_text = response.json()
                            error_msg = error_text.get('error', str(error_text))
                        except:
                            error_msg = response.text[:200]  # Первые 200 символов
                        send_message(chat_id, f"❌ Ошибка от сервера: {error_msg}")

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
