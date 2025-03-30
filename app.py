from flask import Flask, request, abort
from bot import bot
from config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
import telebot
import os

app = Flask(__name__)

# Обработчик вебхуков
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

# Проверка работоспособности
@app.route('/')
def index():
    return 'Bot is running'

if __name__ == "__main__":
    # Удаляем вебхук перед установкой нового
    bot.remove_webhook()
    # Устанавливаем вебхук
    bot.set_webhook(url=WEBHOOK_URL)
    # Запускаем Flask сервер
    app.run(host=WEBAPP_HOST, port=int(os.environ.get('PORT', WEBAPP_PORT))) 