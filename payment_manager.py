from urllib.parse import urlencode
from config import WEBHOOK_HOST  # Вернем импорт WEBHOOK_HOST

class PaymentManager:
    def __init__(self):
        self.wallet = "4100117527556990"  # Номер кошелька ЮMoney
        self.amount = 2.00  # Сумма в рублях (уберем это значение)
        self.price = 100  # Начальная цена за 10 попыток
        self.firebase_manager = None  # Инициализируем в конструкторе, если используете Firebase

    def update_price(self, new_price: float) -> bool:
        """Обновляет цену за 10 попыток"""
        try:
            self.amount = float(new_price)  # Теперь обновляем amount вместо price
            # Если вы используете Firebase для хранения цены, добавьте код здесь
            # Например:
            # self.firebase_manager.update_price(new_price)
            return True
        except Exception as e:
            print(f"Error updating price: {str(e)}")
            return False

    def create_payment_link(self, user_id: int) -> str:
        """Создание ссылки на оплату"""
        payment_params = {
            'targets': 'Анализ отзывов WB',
            'default-sum': self.amount,  # Используем обновленную сумму
            'button-text': 'pay',
            'any-card-payment-type': 'on',
            'button-size': 'm',
            'button-color': 'orange',
            'mail': 'on',
            'successURL': f'{WEBHOOK_HOST}/webhook/payment-success?userId={user_id}',
            'quickpay-form': 'shop',
            'account': self.wallet,
            'label': f'wb_review_bot_{user_id}',
            'need-fio': 'false',
            'need-email': 'false',
            'need-phone': 'false',
            'redirect': 'true',
            'clearCache': 'true',
            'autoReturn': 'true',
            'targets-hint': '',
            'return-url': f'{WEBHOOK_HOST}/webhook/payment-success?userId={user_id}'
        }
        
        return f"https://yoomoney.ru/quickpay/button-widget?{urlencode(payment_params)}"

    def get_payment_message(self) -> tuple[str, str]:
        """Возвращает сообщение с инструкцией и текст для кнопки"""
        message = (
            "❌ У вас закончились попытки анализа!\n\n"
            f"💰 Стоимость 10 попыток - {self.amount}₽\n"
            "После оплаты попытки будут начислены автоматически"
        )
        button_text = f"💳 Оплатить {self.amount}₽"
        return message, button_text

    def verify_payment(self, notification_data: dict) -> tuple[bool, int]:
        """Проверка уведомления об оплате"""
        try:
            # Проверяем сумму
            amount = float(notification_data.get('amount', 0))
            if amount != self.amount:  # Сравниваем с текущей ценой
                return False, 0

            # Получаем ID пользователя из label
            label = notification_data.get('label', '')
            if not label.startswith('wb_review_bot_'):
                return False, 0

            user_id = int(label.split('_')[-1])
            return True, user_id

        except Exception:
            return False, 0 