import telebot
from config import BOT_TOKEN, WEBHOOK_URL

def main():
    bot = telebot.TeleBot(BOT_TOKEN)
    
    # Удаляем старый webhook
    bot.remove_webhook()
    
    # Устанавливаем новый webhook
    bot.set_webhook(url=WEBHOOK_URL)
    
    # Получаем информацию о webhook для проверки
    webhook_info = bot.get_webhook_info()
    print(f"Webhook URL: {webhook_info.url}")
    print(f"Has custom certificate: {webhook_info.has_custom_certificate}")
    print(f"Pending update count: {webhook_info.pending_update_count}")
    print(f"Last error date: {webhook_info.last_error_date}")
    print(f"Last error message: {webhook_info.last_error_message}")

if __name__ == '__main__':
    main() 