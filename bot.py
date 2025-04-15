import telebot
import json
import requests
import re
import g4f
from telebot import types
from firebase_manager import FirebaseManager
from payment_manager import PaymentManager
import os
from flask import Flask
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

try:
    # Инициализация менеджеров
    logger.info("Initializing Firebase Manager...")
    firebase_manager = FirebaseManager()
    logger.info("Initializing Payment Manager...")
    payment_manager = PaymentManager()
    logger.info("Managers initialized successfully")
except Exception as e:
    logger.error(f"Error initializing managers: {str(e)}")
    raise

# Добавим список админов (укажите нужные ID)
ADMIN_IDS = [1312244058]  # Замените на реальные ID администраторов

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
        self.item_name = None  # Инициализируем как None
        self.root_id = None
        # Получаем root_id и item_name
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
            response = requests.get(
                f'https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-8144334&spp=30&nm={self.sku}',
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            if response.status_code != 200:
                raise Exception("Не удалось определить id родителя")
            
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
            print(f"Error in get_root_id: {str(e)}")  # Для отладки
            raise Exception(f"Ошибка при получении информации о товаре: {str(e)}")

    def get_review(self) -> json:
        """Получение отзывов"""
        if not self.root_id:
            raise Exception("root_id не установлен")
            
        try:
            response = requests.get(f'https://feedbacks1.wb.ru/feedbacks/v1/{self.root_id}', 
                                  headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                if not response.json()["feedbacks"]:
                    raise Exception("Сервер 1 не подошел")
                return response.json()
        except Exception:
            response = requests.get(f'https://feedbacks2.wb.ru/feedbacks/v1/{self.root_id}', 
                                  headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                return response.json()

    def parse(self):
        json_feedbacks = self.get_review()
        if not json_feedbacks:
            return []
        feedbacks = [feedback.get("text") for feedback in json_feedbacks["feedbacks"]
                     if str(feedback.get("nmId")) == self.sku]
        if len(feedbacks) > 80:
            feedbacks = feedbacks[:80]
        return feedbacks

def analyze_reviews(reviews_list):
    """Анализирует отзывы с помощью G4F"""
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
    
    try:
        # Используем провайдера Blackbox и модель deepseek
        response = g4f.ChatCompletion.create(
            model="deepseek",
            provider=g4f.Provider.Blackbox,
            messages=[{"role": "user", "content": prompt}],
            timeout=60  # Увеличиваем таймаут для надежности
        )
        # Удаляем рекламные ссылки из ответа
        cleaned_response = re.sub(r'https?://\S+', '', response)
        # Ограничиваем длину ответа
        if len(cleaned_response) > 2500:
            cleaned_response = cleaned_response[:2500] + "..."
        return cleaned_response.strip()
    except Exception as e:
        logger.error(f"Error with Blackbox/deepseek: {str(e)}")
        try:
            # Пробуем запасной вариант - другие провайдеры
            fallback_providers = [
                g4f.Provider.DeepAi,
                g4f.Provider.GptGo,
                g4f.Provider.You,
                g4f.Provider.ChatBase
            ]
            
            for provider in fallback_providers:
                try:
                    logger.info(f"Trying fallback provider: {provider.__name__}")
                    response = g4f.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        provider=provider,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=30
                    )
                    cleaned_response = re.sub(r'https?://\S+', '', response)
                    if len(cleaned_response) > 2500:
                        cleaned_response = cleaned_response[:2500] + "..."
                    return cleaned_response.strip()
                except Exception as e2:
                    logger.error(f"Error with fallback provider {provider.__name__}: {str(e2)}")
                    continue
            
            # Если все запасные провайдеры не сработали, возвращаем ошибку
            return f"Не удалось выполнить анализ отзывов: {str(e)}"
        except Exception as e3:
            return f"Не удалось выполнить анализ отзывов: {str(e3)}"

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "пользователь"
        
        # Получаем количество доступных попыток
        attempts = firebase_manager.get_user_attempts(user_id)
        
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
        bot.reply_to(message, welcome_text, reply_markup=markup)
        
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")
        bot.reply_to(message, "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.")

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
        # Здесь добавьте код для сохранения новой цены в вашей системе
        # Например, через PaymentManager или Firebase
        payment_manager.update_price(new_price)  # Предполагается, что такой метод существует
        
        bot.reply_to(message, f"✅ Цена успешно обновлена до {new_price} рублей за 10 попыток")
        # Показываем стартовое меню
        start(message)
    except ValueError:
        bot.reply_to(message, "❌ Пожалуйста, введите корректное число")
        start(message)

# Обновим существующий обработчик сообщений, добавив проверку на состояние
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text.isdigit() or 'wildberries' in message.text.lower():
        user_id = message.from_user.id
        text = message.text
        
        # Проверка количества попыток
        attempts = firebase_manager.get_user_attempts(user_id)
        if attempts <= 0:
            # Создаем клавиатуру с кнопкой оплаты
            markup = types.InlineKeyboardMarkup()
            payment_msg, button_text = payment_manager.get_payment_message()
            payment_button = types.InlineKeyboardButton(
                button_text,
                url=payment_manager.create_payment_link(user_id)
            )
            markup.add(payment_button)
            
            bot.reply_to(
                message,
                payment_msg,
                reply_markup=markup
            )
            return
        
        # Отправка сообщения о начале анализа
        processing_msg = bot.reply_to(
            message, 
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
            remaining_attempts = firebase_manager.decrease_attempts(user_id)
            
            # Добавляем информацию об оставшихся попытках
            analysis_with_attempts = (
                f"{analysis}\n\n"
                f"Осталось попыток: {remaining_attempts}"
            )
            
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
                        if i == 0:
                            header = "📊 Анализ отзывов (часть 1 из {})\n\n".format(len(message_parts))
                            # Проверяем длину сообщения перед отправкой
                            if len(header + part) > 4000:
                                shortened_part = part[:3950 - len(header)] + "..."
                                bot.send_message(message.chat.id, header + shortened_part)
                            else:
                                bot.send_message(message.chat.id, header + part)
                        else:
                            header = "📊 Анализ отзывов (часть {} из {})\n\n".format(i+1, len(message_parts))
                            # Проверяем длину сообщения перед отправкой
                            if len(header + part) > 4000:
                                shortened_part = part[:3950 - len(header)] + "..."
                                bot.send_message(message.chat.id, header + shortened_part)
                            else:
                                bot.send_message(message.chat.id, header + part)
                    except Exception as e:
                        logger.error(f"Error sending message part {i+1}: {str(e)}")
                        bot.send_message(
                            message.chat.id, 
                            f"⚠️ Не удалось отправить часть {i+1} анализа из-за ошибки: {str(e)}"
                        )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            bot.edit_message_text(f"❌ Произошла ошибка: {str(e)}", 
                                chat_id=message.chat.id,
                                message_id=processing_msg.message_id)
    else:
        bot.reply_to(message, "❌ Пожалуйста, отправьте корректную ссылку на товар с Wildberries или артикул товара.")

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