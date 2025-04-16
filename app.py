from flask import Flask, request, abort, redirect
from bot import bot, logger, firebase_manager
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
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

# Обработка вебхуков на корневом маршруте
@app.route('/', methods=['POST'])
def root_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        logger.info(f"Received webhook to root path: {json_string[:100]}...")  # Логируем только начало для безопасности
        
        try:
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        except Exception as e:
            logger.error(f"Error processing update at root path: {str(e)}")
            abort(500)
    else:
        logger.warning(f"Received request to root with invalid content-type: {request.headers.get('content-type')}")
        abort(403)

# Обработчик успешной оплаты
@app.route('/webhook/payment-success', methods=['GET'])
def payment_success():
    user_id = request.args.get('userId')
    logger.info(f"Payment success webhook called for user: {user_id}")
    
    if not user_id:
        logger.error("No userId provided in payment success webhook")
        return "Error: No user ID provided", 400
    
    try:
        # Добавляем попытки пользователю
        user_id = int(user_id)
        firebase_manager.add_attempts(user_id, 10)
        
        # Отправляем сообщение пользователю
        bot.send_message(
            user_id,
            "✅ Оплата успешно проведена!\n\n"
            "Вам начислено 10 попыток. Вы можете продолжить пользоваться ботом."
        )
        
        # Перенаправляем пользователя обратно в Telegram
        return redirect(f"https://t.me/{bot.get_me().username}")
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        return "Error processing payment", 500

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