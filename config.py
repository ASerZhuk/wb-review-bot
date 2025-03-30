import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PATH = '/webhook/telegram'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Конфигурация веб-сервера
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 3000))

def format_firebase_key(key: str) -> str:
    """Форматирует приватный ключ Firebase"""
    if not key:
        return ''
    # Удаляем лишние кавычки в начале и конце
    key = key.strip('"\'')
    # Заменяем экранированные переносы строк на реальные
    key = key.replace('\\n', '\n')
    return key

# Конфигурация Firebase
FIREBASE_CREDENTIALS_JSON = {
    "type": "service_account",
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": format_firebase_key(os.getenv('FIREBASE_PRIVATE_KEY', '')),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
    "universe_domain": "googleapis.com"
}

# Добавим проверку приватного ключа
if not FIREBASE_CREDENTIALS_JSON['private_key'].startswith('-----BEGIN PRIVATE KEY-----'):
    print("WARNING: Firebase private key appears to be malformed!")
    print(f"Key starts with: {FIREBASE_CREDENTIALS_JSON['private_key'][:50]}...")

# Конфигурация ЮMoney
YOOMONEY_WALLET = os.getenv('YOOMONEY_WALLET')
YOOMONEY_AMOUNT = float(os.getenv('YOOMONEY_AMOUNT', 100.00))