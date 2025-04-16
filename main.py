from flask import Flask, request, abort, redirect, jsonify
from bot import bot, logger, firebase_manager
from config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from flask_cors import CORS
import telebot
import os
import sys
import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)
CORS(app)  # Включаем CORS для всех маршрутов
logger.info("Flask app initialized")

# Инициализация вебхука при старте
try:
    logger.info("Initializing webhook on startup...")
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    webhook_info = bot.get_webhook_info()
    logger.info(f"Webhook status: URL={webhook_info.url}, pending_updates={webhook_info.pending_update_count}")
except Exception as e:
    logger.error(f"Failed to initialize webhook: {e}")

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
        logger.info(f"Received webhook to root path: {json_string[:100]}...")
        
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

# Очень простой health check для Timeweb Cloud
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'port': 80,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }), 200

# Дополнительный endpoint для проверки порта
@app.route('/port', methods=['GET'])
def port_check():
    return jsonify({
        'port': 80,
        'server': 'running'
    }), 200

if __name__ == "__main__":
    logger.info("Starting Flask server in development mode...")
    try:
        # Запуск только при прямом вызове python main.py (не через gunicorn)
        port = 80
        logger.info(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logging.error(f"Failed to start server: {e}") 