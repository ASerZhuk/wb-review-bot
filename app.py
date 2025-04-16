from flask import Flask, request, abort, redirect, jsonify
from bot import bot, logger, firebase_manager
from config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
import telebot
import os
import sys

app = Flask(__name__)

# Обработчик вебхуков
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        logger.info(f"Received webhook: {json_string[:100]}...")
        
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
    try:
        # Проверяем основные переменные окружения
        env_vars = {
            'BOT_TOKEN': bool(os.getenv('BOT_TOKEN')),
            'WEBHOOK_HOST': os.getenv('WEBHOOK_HOST'),
            'FIREBASE_PROJECT_ID': bool(os.getenv('FIREBASE_PROJECT_ID')),
            'WEBHOOK_PATH': WEBHOOK_PATH,
            'WEBHOOK_URL': WEBHOOK_URL
        }
        
        # Проверяем webhook
        try:
            webhook_info = bot.get_webhook_info()
            webhook_status = {
                'url': webhook_info.url,
                'has_custom_certificate': webhook_info.has_custom_certificate,
                'pending_update_count': webhook_info.pending_update_count,
                'last_error_date': webhook_info.last_error_date,
                'last_error_message': webhook_info.last_error_message
            }
        except Exception as e:
            webhook_status = {'error': str(e)}

        return jsonify({
            'status': 'running',
            'environment': env_vars,
            'webhook': webhook_status,
            'python_version': sys.version,
            'bot_info': bot.get_me().__dict__
        })
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

def init_webhook():
    """Инициализация вебхука"""
    try:
        logger.info("Removing existing webhook...")
        bot.remove_webhook()
        
        logger.info(f"Setting webhook to {WEBHOOK_URL}")
        bot.set_webhook(url=WEBHOOK_URL)
        
        webhook_info = bot.get_webhook_info()
        if webhook_info.url == WEBHOOK_URL:
            logger.info("Webhook set successfully")
            return True
        else:
            logger.error(f"Webhook URL mismatch. Expected: {WEBHOOK_URL}, Got: {webhook_info.url}")
            return False
    except Exception as e:
        logger.error(f"Error setting webhook: {str(e)}")
        return False

@app.before_first_request
def setup_webhook():
    logger.info("Setting up webhook before first request...")
    init_webhook()

if __name__ == "__main__":
    logger.info("Starting Flask server...")
    try:
        app.run(host=WEBAPP_HOST, port=int(os.environ.get('PORT', WEBAPP_PORT)))
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise 