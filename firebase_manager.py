import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
from config import FIREBASE_CREDENTIALS_JSON
import logging

logger = logging.getLogger(__name__)

class FirebaseManager:
    def __init__(self):
        try:
            logger.info("Starting Firebase initialization...")
            logger.info(f"Project ID: {FIREBASE_CREDENTIALS_JSON.get('project_id')}")
            logger.info(f"Client Email: {FIREBASE_CREDENTIALS_JSON.get('client_email')}")
            
            # Проверяем, не инициализирован ли уже Firebase
            if not firebase_admin._apps:
                # Проверяем наличие всех необходимых полей
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if not FIREBASE_CREDENTIALS_JSON.get(field)]
                
                if missing_fields:
                    raise ValueError(f"Missing required fields in Firebase credentials: {', '.join(missing_fields)}")
                
                logger.info("Creating Firebase credentials...")
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_JSON)
                logger.info("Initializing Firebase app...")
                firebase_admin.initialize_app(cred)
                logger.info("Firebase app initialized successfully")
            else:
                logger.info("Firebase already initialized")
            
            self.db = firestore.client()
            logger.info("Firestore client created successfully")
            
        except Exception as e:
            logger.error(f"Firebase initialization error: {str(e)}")
            logger.error("Firebase credentials:")
            for key, value in FIREBASE_CREDENTIALS_JSON.items():
                if key != 'private_key':
                    logger.error(f"{key}: {value}")
                else:
                    logger.error(f"private_key length: {len(str(value))}")
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