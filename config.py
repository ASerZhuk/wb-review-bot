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
WEBAPP_PORT = int(os.getenv('PORT',8080))

def get_env_var(name: str, required: bool = True) -> str:
    """Получение переменной окружения с логированием"""
    value = os.getenv(name)
    if required and not value:
        logger.error(f"Missing required environment variable: {name}")
        raise ValueError(f"Missing required environment variable: {name}")
    logger.info(f"Environment variable {name} {'found' if value else 'not found'}")
    return value or ''

# Конфигурация ЮMoney
YOOMONEY_WALLET = os.getenv('YOOMONEY_WALLET')
YOOMONEY_AMOUNT = float(os.getenv('YOOMONEY_AMOUNT', 100.00))