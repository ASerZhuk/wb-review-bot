import telebot
import json
import requests
import re
import g4f
from telebot import types
from firebase_manager import FirebaseManager
from payment_manager import PaymentManager

# Инициализация бота
BOT_TOKEN = '7909512676:AAHqSHHpM6QkJdGsisH9lbiv5-o4Veuv3oI'
bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# Инициализация менеджеров
firebase_manager = FirebaseManager()
payment_manager = PaymentManager()

# Добавим список админов (укажите нужные ID)
ADMIN_IDS = [1312244058]  # Замените на реальные ID администраторов

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
    На основе следующих отзывов с Wildberries сделай подробный анализ товара.
    Отзывы:
    {reviews_text}
    
    Пожалуйста, структурируй ответ следующим образом:
    
    ✅ ПЛЮСЫ ТОВАРА:
    - [перечисли кратко основные плюсы, которые часто упоминаются в отзывах, тезисно]

    ❌ МИНУСЫ ТОВАРА:
    - [перечисли кратко основные минусы и недостататков из отзывов, тезисно]

    📝 ОБЩИЙ ВЫВОД:
    [краткое заключение о товаре в 1 предложениe]
    
    Пожалуйста, не добавляй никаких ссылок или рекламы в ответ. 
    """
    
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        # Удаляем рекламные ссылки из ответа
        cleaned_response = re.sub(r'https?://\S+', '', response)
        return cleaned_response.strip()
    except Exception as e:
        try:
            # Пробуем другую модель, если первая не сработала
            response = g4f.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            # Удаляем рекламные ссылки из ответа
            cleaned_response = re.sub(r'https?://\S+', '', response)
            return cleaned_response.strip()
        except Exception as e2:
            return f"Не удалось выполнить анализ отзывов: {str(e2)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    
    # Кнопка анализа товаров для всех пользователей
    analyze_button = types.InlineKeyboardButton("📊 Анализ товара", callback_data="analyze")
    markup.add(analyze_button)
    
    # Добавляем кнопку админ-панели только для администраторов
    if user_id in ADMIN_IDS:
        admin_button = types.InlineKeyboardButton("⚙️ Админ панель", callback_data="admin_panel")
        markup.add(admin_button)
    
    bot.reply_to(message, 
        "👋 Привет! Я бот для анализа товаров на Wildberries.\n\n"
        "🔍 Выберите действие:", 
        reply_markup=markup)

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
        send_welcome(message)
    except ValueError:
        bot.reply_to(message, "❌ Пожалуйста, введите корректное число")
        send_welcome(message)

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
            
            # Отправка результата
            bot.edit_message_text(
                analysis_with_attempts,
                chat_id=message.chat.id,
                message_id=processing_msg.message_id
            )
            
        except Exception as e:
            bot.edit_message_text(f"❌ Произошла ошибка: {str(e)}", 
                                chat_id=message.chat.id,
                                message_id=processing_msg.message_id)
    else:
        bot.reply_to(message, "❌ Пожалуйста, отправьте корректную ссылку на товар с Wildberries или артикул товара.")

if __name__ == '__main__':
    bot.polling(none_stop=False) 