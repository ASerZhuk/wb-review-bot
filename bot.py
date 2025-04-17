import telebot
import json
import requests
import re
import g4f
from g4f.Provider import Blackbox, DDG, PollinationsAI
from telebot import types
from database_manager import DatabaseManager  # Changed from FirebaseManager
from payment_manager import PaymentManager
import os
from flask import Flask
import logging
import random
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Список User-Agent для ротации
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1'
]

def get_random_headers():
    """Генерирует случайные заголовки для запроса"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

# Инициализация бота
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

try:
    # Инициализация менеджеров
    logger.info("Initializing Database Manager...")
    database_manager = DatabaseManager()  # Changed from FirebaseManager
    logger.info("Initializing Payment Manager...")
    payment_manager = PaymentManager()
    # Устанавливаем связь между менеджерами
    payment_manager.set_database_manager(database_manager)  # Changed from set_firebase_manager
    logger.info("Managers initialized successfully")
except Exception as e:
    logger.error(f"Error initializing managers: {str(e)}")
    raise

# Добавим список админов (укажите нужные ID)
ADMIN_IDS = [1312244058]  # Замените на реальные ID администраторов
logger.info(f"Admin IDs: {ADMIN_IDS}")

# Функция для разделения длинных сообщений
def split_long_message(text, max_length=3000):
    """Разделяет длинное сообщение на части, чтобы не превышать лимиты Telegram"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем по абзацам, чтобы не разрывать текст посреди предложения
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # Если добавление абзаца превысит максимальную длину, сохраняем текущую часть
        if len(current_part) + len(paragraph) + 2 > max_length:
            parts.append(current_part.strip())
            current_part = paragraph + "\n\n"
        else:
            current_part += paragraph + "\n\n"
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part.strip())
    
    return parts

class WbReview:
    def __init__(self, string: str):
        self.sku = self.get_sku(string=string)
        self.item_name = None
        self.root_id = None
        self.get_root_id()

    @staticmethod
    def get_sku(string: str) -> str:
        """Получение артикула"""
        if "wildberries" in string:
            pattern = r"\d{7,15}"
            sku = re.findall(pattern, string)
            if sku:
                return sku[0]
            else:
                raise Exception("Не удалось найти артикул")
        return string

    def get_root_id(self):
        """Получение id родителя и названия товара"""
        try:
            # Увеличиваем задержку между запросами
            time.sleep(random.uniform(2, 5))  # Увеличено с 1-3 до 2-5 секунд
            
            headers = get_random_headers()
            response = requests.get(
                f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-8144334&spp=30&nm={self.sku}',
                headers=headers,
                timeout=15  # Увеличено время ожидания
            )
            
            # Обработка ошибки 429 (Too Many Requests)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 30))
                logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                time.sleep(retry_after + 5)  # Добавляем дополнительное время
                return self.get_root_id()  # Рекурсивный повтор запроса
            
            if response.status_code == 403:
                time.sleep(random.uniform(3, 6))  # Увеличено время ожидания
                headers = get_random_headers()
                response = requests.get(
                    f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-8144334&spp=30&nm={self.sku}',
                    headers=headers,
                    timeout=15
                )
            
            if response.status_code != 200:
                raise Exception(f"Не удалось определить id родителя. Код ответа: {response.status_code}")
            
            data = response.json()
            if not data.get("data") or not data["data"].get("products") or len(data["data"]["products"]) == 0:
                raise Exception("Товар не найден")
            
            product = data["data"]["products"][0]
            self.item_name = product.get("name", "Название не найдено")
            self.root_id = product.get("root")
            if not self.root_id:
                raise Exception("Не удалось получить root_id товара")
            return self.root_id
        except Exception as e:
            logger.error(f"Error in get_root_id: {str(e)}")
            raise Exception(f"Ошибка при получении информации о товаре: {str(e)}")

    def get_review(self) -> json:
        """Получение отзывов"""
        if not self.root_id:
            raise Exception("root_id не установен")
            
        try:
            # Увеличиваем задержку между запросами
            time.sleep(random.uniform(3, 6))  # Увеличено с 1-3 до 3-6 секунд
            
            headers = get_random_headers()
            response = requests.get(
                f'https://feedbacks1.wb.ru/feedbacks/v1/{self.root_id}',
                headers=headers,
                timeout=15
            )
            
            # Обработка ошибки 429 (Too Many Requests)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 30))
                logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds...")
                time.sleep(retry_after + 5)  # Добавляем дополнительное время
                return self.get_review()  # Рекурсивный повтор запроса
            
            if response.status_code == 403:
                time.sleep(random.uniform(4, 8))  # Увеличено время ожидания
                headers = get_random_headers()
                response = requests.get(
                    f'https://feedbacks1.wb.ru/feedbacks/v1/{self.root_id}',
                    headers=headers,
                    timeout=15
                )
            
            if response.status_code == 200:
                if not response.json().get("feedbacks"):
                    raise Exception("Сервер 1 не подошел")
                return response.json()
            
            # Пробуем второй сервер после задержки
            time.sleep(random.uniform(4, 8))
            headers = get_random_headers()
            response = requests.get(
                f'https://feedbacks1.wb.ru/feedbacks/v2/{self.root_id}',
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Не удалось получить отзывы. Код ответа: {response.status_code}")
        except Exception as e:
            logger.error(f"Error in get_review: {str(e)}")
            raise Exception(f"Ошибка при получении отзывов: {str(e)}")

    def parse(self):
        try:
            json_feedbacks = self.get_review()
            if not json_feedbacks:
                return []
                
            feedbacks = [feedback.get("text") for feedback in json_feedbacks["feedbacks"]
                         if str(feedback.get("nmId")) == self.sku]
            if len(feedbacks) > 80:
                feedbacks = feedbacks[:80]
            return feedbacks
        except Exception as e:
            logger.error(f"Error in parse: {str(e)}")
            raise Exception(f"Ошибка при обработке отзывов: {str(e)}")

def analyze_reviews(reviews_list):
    """Анализирует отзывы с помощью G4F"""
    if not reviews_list:
        return "❌ Не найдено отзывов для анализа"

    reviews_text = "\n\n".join(reviews_list)
    prompt = f"""
    На основе следующих отзывов с Wildberries сделай ОЧЕНЬ КРАТКИЙ анализ товара не более 1500 символов.
    Отзывы:
    {reviews_text}
    
    Пожалуйста, структурируй ответ следующим образом:
    
    ✅ ПЛЮСЫ ТОВАРА:
    - [перечисли только 3-4 самых важных плюсов очень кратко, одной строкой каждый]

    ❌ МИНУСЫ ТОВАРА:
    - [перечисли только 3-4 самых важных минусов очень кратко, одной строкой каждый]

    📝 ОБЩИЙ ВЫВОД:
    [краткое заключение о товаре в 1 предложениe]
    
    ВАЖНО: Ответ должен быть максимально лаконичным, не более 1500 символов в итоге.
    Не добавляй лишней информации и не используй длинные формулировки.
    """
    
    # Список провайдеров для попытки
    providers = [
        Blackbox,
        DDG, 
        PollinationsAI
        
    ]
    
    last_error = None
    for provider in providers:
        try:
            logger.info(f"Trying provider {provider.__name__}")
            response = g4f.ChatCompletion.create(
                model="dgpt-4o-mini",  # Используем только модель deepseek-v3
                provider=provider,
                messages=[{"role": "user", "content": prompt}],
                timeout=60
            )
            # Удаляем рекламные ссылки из ответа
            cleaned_response = re.sub(r'https?://\S+', '', response)
            # Ограничиваем длину ответа
            if len(cleaned_response) > 2500:
                cleaned_response = cleaned_response[:2500] + "..."
            return cleaned_response.strip()
        except Exception as e:
            last_error = e
            logger.error(f"Error with provider {provider.__name__}: {str(e)}")
            continue
    
    # Если все провайдеры не сработали
    error_msg = str(last_error) if last_error else "неизвестная ошибка"
    logger.error(f"All providers failed. Last error: {error_msg}")
    return f"❌ Не удалось выполнить анализ отзывов. Пожалуйста, попробуйте позже.\nОшибка: {error_msg}"

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "пользователь"
        
        # Получаем количество доступных попыток
        attempts = database_manager.get_user_attempts(user_id)  # Changed from firebase_manager
        
        welcome_text = (
            f"👋 Привет, {username}!\n\n"
            "Я помогу проанализировать отзывы с Wildberries. "
            "Просто отправь мне ссылку на товар или его артикул.\n\n"
            f"У тебя есть {attempts} попыток для анализа."
        )
        
        # Создаем клавиатуру с кнопкой оплаты, если попытки закончились
        markup = None
        if attempts <= 0:
            markup = types.InlineKeyboardMarkup()
            payment_msg, button_text = payment_manager.get_payment_message()
            payment_button = types.InlineKeyboardButton(
                button_text,
                url=payment_manager.create_payment_link(user_id)
            )
            markup.add(payment_button)
            welcome_text += f"\n\n{payment_msg}"
        
        logger.info(f"Sending welcome message to user {user_id}")
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
        
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")
        bot.send_message(message.chat.id, "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.")

# Добавим обработчик callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "analyze":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, 
            "Отправьте мне ссылку на товар с Wildberries или артикул товара, "
            "и я проанализирую отзывы, чтобы выделить основные плюсы и минусы товара.")
    
    elif call.data == "admin_panel" and call.from_user.id in ADMIN_IDS:
        bot.answer_callback_query(call.id)
        show_admin_panel(call.message)
    
    elif call.data == "change_price" and call.from_user.id in ADMIN_IDS:
        bot.answer_callback_query(call.id)
        ask_new_price(call.message)

def show_admin_panel(message):
    markup = types.InlineKeyboardMarkup()
    change_price_button = types.InlineKeyboardButton("💰 Изменить цену за 10 попыток", callback_data="change_price")
    back_button = types.InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")
    markup.add(change_price_button)
    markup.add(back_button)
    
    bot.edit_message_text(
        "⚙️ Админ-панель\n\nВыберите действие:",
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=markup
    )

def ask_new_price(message):
    msg = bot.edit_message_text(
        "💰 Введите новую цену за 10 попыток (только число):",
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    bot.register_next_step_handler(msg, process_new_price)

def process_new_price(message):
    try:
        new_price = float(message.text)
        payment_manager.update_price(new_price)  # Теперь работает с SQLite
        
        bot.send_message(message.chat.id, f"✅ Цена успешно обновлена до {new_price} рублей за 10 попыток")
        # Показываем стартовое меню
        start(message)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число")
        start(message)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """Обработчик команды /admin для вызова админ-панели"""
    user_id = message.from_user.id
    logger.info(f"Admin command received from user {user_id}")
    
    # Проверяем, является ли пользователь администратором
    if user_id in ADMIN_IDS:
        logger.info(f"User {user_id} is in admin list, showing admin panel")
        # Создаем клавиатуру с административными функциями
        markup = types.InlineKeyboardMarkup()
        change_price_button = types.InlineKeyboardButton("💰 Изменить цену за 10 попыток", callback_data="change_price")
        markup.add(change_price_button)
        
        bot.send_message(
            message.chat.id,
            "⚙️ Админ-панель\n\nВыберите действие:",
            reply_markup=markup
        )
    else:
        logger.info(f"User {user_id} is NOT in admin list {ADMIN_IDS}")
        # Если пользователь не администратор, отправляем сообщение об ошибке доступа
        bot.send_message(message.chat.id, "❌ У вас нет доступа к административной панели.")

@bot.message_handler(commands=['myid'])
def my_id_command(message):
    """Показывает пользователю его ID"""
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"Ваш ID: {user_id}")

# Обновим существующий обработчик сообщений, добавив проверку на состояние
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_message(message):
    if message.text.isdigit() or 'wildberries' in message.text.lower():
        user_id = message.from_user.id
        text = message.text
        
        # Проверка количества попыток
        attempts = database_manager.get_user_attempts(user_id)  # Changed from firebase_manager
        if attempts <= 0:
            # Создаем клавиатуру с кнопкой оплаты
            markup = types.InlineKeyboardMarkup()
            payment_msg, button_text = payment_manager.get_payment_message()
            payment_button = types.InlineKeyboardButton(
                button_text,
                url=payment_manager.create_payment_link(user_id)
            )
            markup.add(payment_button)
            
            bot.send_message(
                message.chat.id,
                payment_msg,
                reply_markup=markup
            )
            return
        
        # Отправка сообщения о начале анализа
        processing_msg = bot.send_message(
            message.chat.id, 
            f"⏳ Анализирую отзывы... Это может занять некоторое время.\n"
            f"У вас осталось попыток: {attempts}"
        )
        
        try:
            # Получение отзывов
            review_handler = WbReview(text)
            reviews = review_handler.parse()
            
            if not reviews:
                bot.edit_message_text("❌ Не найдено отзывов для данного товара", 
                                    chat_id=message.chat.id, 
                                    message_id=processing_msg.message_id)
                return
                
            # Анализ отзывов
            analysis = analyze_reviews(reviews)
            
            # Уменьшаем количество попыток
            remaining_attempts = database_manager.decrease_attempts(user_id)  # Changed from firebase_manager
            
            # Не добавляем информацию об оставшихся попытках в сообщение с анализом
            analysis_with_attempts = analysis
            
            # Разбиваем сообщение, если оно слишком длинное
            message_parts = split_long_message(analysis_with_attempts)
            
            # Отправка результата
            if len(message_parts) == 1:
                # Если сообщение помещается в один блок, используем edit_message_text
                bot.edit_message_text(
                    message_parts[0],
                    chat_id=message.chat.id,
                    message_id=processing_msg.message_id
                )
            else:
                # Если сообщение длинное, удаляем предыдущее и отправляем по частям
                bot.delete_message(message.chat.id, processing_msg.message_id)
                
                # Добавляем обработку ошибок при отправке каждой части
                for i, part in enumerate(message_parts):
                    try:
                        # Отправляем части без заголовков
                        # Проверяем длину сообщения перед отправкой
                        if len(part) > 4000:
                            shortened_part = part[:3950] + "..."
                            bot.send_message(message.chat.id, shortened_part)
                        else:
                            bot.send_message(message.chat.id, part)
                    except Exception as e:
                        logger.error(f"Error sending message part {i+1}: {str(e)}")
                        bot.send_message(
                            message.chat.id, 
                            f"⚠️ Не удалось отправить часть анализа из-за ошибки: {str(e)}"
                        )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            bot.edit_message_text(f"❌ Произошла ошибка: {str(e)}", 
                                chat_id=message.chat.id,
                                message_id=processing_msg.message_id)
    else:
        bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте корректную ссылку на товар с Wildberries или артикул товара.")

if __name__ == '__main__':
    logger.info("Starting bot...")
    if os.environ.get('WEBHOOK_ENABLED', 'false').lower() == 'true':
        # Если включен режим вебхуков, сервер запускается через app.py
        logger.info("Webhook mode enabled")
        pass
    else:
        # Если вебхуки выключены, используем polling
        logger.info("Starting polling mode")
        bot.remove_webhook()
        bot.polling(none_stop=True)