import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FirebaseManager:
    def __init__(self):
        try:
            logger.info("Starting Firebase initialization...")
            
            # Проверяем, не инициализирован ли уже Firebase
            if not firebase_admin._apps:
                # Пробуем использовать JSON-файл напрямую
                cred_path = 'serviceAccountKey.json'
                
                if os.path.exists(cred_path):
                    logger.info(f"Using credentials from {cred_path}")
                    cred = credentials.Certificate(cred_path)
                else:
                    # Если файл не найден, используем переменные окружения
                    logger.info(f"Credentials file not found, using environment variables")
                    from config import load_firebase_credentials
                    firebase_creds = load_firebase_credentials()
                    cred = credentials.Certificate(firebase_creds)
                
                logger.info("Initializing Firebase app...")
                firebase_admin.initialize_app(cred)
                logger.info("Firebase app initialized successfully")
            else:
                logger.info("Firebase already initialized")
            
            self.db = firestore.client()
            logger.info("Firestore client created successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization error: {str(e)}")
            raise

    def get_user_attempts(self, user_id: int) -> int:
        """Получение количества оставшихся попыток пользователя"""
        try:
            doc_ref = self.db.collection('users').document(str(user_id))
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get('attempts', 0)
            else:
                # Создаем нового пользователя с 1 попыткой
                doc_ref.set({
                    'user_id': user_id,
                    'attempts': 1,
                    'created_at': datetime.now(),
                    'total_attempts_used': 0
                })
                return 1
        except Exception as e:
            logger.error(f"Error in get_user_attempts: {str(e)}")
            return 0

    def decrease_attempts(self, user_id: int) -> int:
        """Уменьшение количества попыток"""
        doc_ref = self.db.collection('users').document(str(user_id))
        doc = doc_ref.get()
        if doc.exists:
            attempts = doc.to_dict().get('attempts', 0)
            total_used = doc.to_dict().get('total_attempts_used', 0)
            if attempts > 0:
                doc_ref.update({
                    'attempts': attempts - 1,
                    'total_attempts_used': total_used + 1,
                    'last_used': datetime.now()
                })
                return attempts - 1
        return 0

    def add_attempts(self, user_id: int, amount: int = 10):
        """Добавление попыток после оплаты"""
        doc_ref = self.db.collection('users').document(str(user_id))
        doc = doc_ref.get()
        current_attempts = doc.to_dict().get('attempts', 0) if doc.exists else 0
        total_purchased = doc.to_dict().get('total_purchased', 0) if doc.exists else 0
        
        doc_ref.set({
            'user_id': user_id,
            'attempts': current_attempts + amount,
            'total_purchased': total_purchased + amount,
            'last_purchase': datetime.now(),
            'updated_at': datetime.now()
        }, merge=True)

    def get_price(self) -> float:
        """Получает текущую цену за 10 попыток из Firebase"""
        try:
            price_doc = self.db.collection('settings').document('prices').get()
            if price_doc.exists:
                return float(price_doc.to_dict().get('attempts_10', 100))
            else:
                # Если документ не существует, создаем его с ценой по умолчанию
                self.db.collection('settings').document('prices').set({
                    'attempts_10': 100,
                    'created_at': datetime.now()
                })
                return 100.0
        except Exception as e:
            logger.error(f"Error getting price: {str(e)}")
            return 100.0  # Возвращаем цену по умолчанию в случае ошибки

    def update_price(self, new_price: float) -> bool:
        """Обновляет цену за 10 попыток в Firebase"""
        try:
            self.db.collection('settings').document('prices').set({
                'attempts_10': float(new_price),
                'updated_at': datetime.now()
            }, merge=True)
            logger.info(f"Price updated to {new_price}")
            return True
        except Exception as e:
            logger.error(f"Error updating price: {str(e)}")
            return False 