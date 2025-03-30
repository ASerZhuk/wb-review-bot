from flask import Flask, request, abort
from bot import bot, logger
from config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
import telebot
import os

app = Flask(__name__)

# Обработчик вебхуков
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        logger.info(f"Received webhook: {json_string[:100]}...")  # Логируем только начало для безопасности
        
        try:
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            abort(500)
    else:
        logger.warning(f"Received request with invalid content-type: {request.headers.get('content-type')}")
        abort(403)

# Проверка работоспособности
@app.route('/')
def index():
    return 'Bot is running'

if __name__ == "__main__":
    logger.info("Starting Flask server...")
    try:
        # Удаляем вебхук перед установкой нового
        bot.remove_webhook()
        # Устанавливаем вебхук
        bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set to {WEBHOOK_URL}")
        # Запускаем Flask сервер
        app.run(host=WEBAPP_HOST, port=int(os.environ.get('PORT', WEBAPP_PORT)))
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise 