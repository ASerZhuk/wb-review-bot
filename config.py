import os
from dotenv import load_dotenv
import logging
import json

logger = logging.getLogger(__name__)

load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')

# Удаляем лишний слеш в конце WEBHOOK_HOST, если он есть
if WEBHOOK_HOST and WEBHOOK_HOST.endswith('/'):
    WEBHOOK_HOST = WEBHOOK_HOST.rstrip('/')
    logger.info(f"Removed trailing slash from WEBHOOK_HOST: {WEBHOOK_HOST}")

WEBHOOK_PATH = '/webhook/telegram'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
# Проверяем, нет ли двойного слеша
if '//' in WEBHOOK_URL and not WEBHOOK_URL.startswith('http'):
    WEBHOOK_URL = WEBHOOK_URL.replace('//', '/')

# Конфигурация веб-сервера
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 3000))

def get_env_var(name: str, required: bool = True) -> str:
    """Получение переменной окружения с логированием"""
    value = os.getenv(name)
    if required and not value:
        logger.error(f"Missing required environment variable: {name}")
        raise ValueError(f"Missing required environment variable: {name}")
    logger.info(f"Environment variable {name} {'found' if value else 'not found'}")
    return value or ''

def load_firebase_credentials():
    """Загрузка учетных данных Firebase из JSON файла"""
    try:
        # Пробуем сначала serviceAccountKey.json
        json_file_path = 'serviceAccountKey.json'
        if not os.path.exists(json_file_path):
            # Пытаемся найти другие файлы firebase-adminsdk*
            logger.info(f"File {json_file_path} not found, checking for alternative credentials file")
            import glob
            firebase_files = glob.glob('*firebase-adminsdk*.json')
            if firebase_files:
                json_file_path = firebase_files[0]
                logger.info(f"Found alternative credentials file: {json_file_path}")
            else:
                logger.warning("No Firebase credentials file found, using environment variables")
                
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                return json.load(f)
        
        # Если файл не найден, используем переменные окружения
        logger.info("Using Firebase credentials from environment variables")
        return {
            "type": os.getenv('FIREBASE_TYPE', 'service_account'),
            "project_id": get_env_var('FIREBASE_PROJECT_ID'),
            "private_key_id": get_env_var('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": get_env_var('FIREBASE_PRIVATE_KEY'),  # Используем ключ как есть, без форматирования
            "client_email": get_env_var('FIREBASE_CLIENT_EMAIL'),
            "client_id": get_env_var('FIREBASE_CLIENT_ID'),
            "auth_uri": os.getenv('FIREBASE_AUTH_URI', "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv('FIREBASE_TOKEN_URI', "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": get_env_var('FIREBASE_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', "googleapis.com")
        }
    except Exception as e:
        logger.error(f"Error loading Firebase credentials: {str(e)}")
        raise

# Конфигурация ЮMoney
YOOMONEY_WALLET = os.getenv('YOOMONEY_WALLET')
YOOMONEY_AMOUNT = float(os.getenv('YOOMONEY_AMOUNT', 100.00))