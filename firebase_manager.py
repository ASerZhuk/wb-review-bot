import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
from config import FIREBASE_CREDENTIALS_JSON

class FirebaseManager:
    def __init__(self):
        try:
            # Инициализация Firebase с помощью словаря учетных данных
            if not firebase_admin._apps:
                if not FIREBASE_CREDENTIALS_JSON.get('private_key'):
                    raise ValueError("Firebase private key is missing")
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_JSON)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization error: {str(e)}")
            raise

    def get_user_attempts(self, user_id: int) -> int:
        """Получение количества оставшихся попыток пользователя"""
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