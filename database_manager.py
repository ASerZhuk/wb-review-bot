import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_name='bot_database.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    attempts INTEGER DEFAULT 1,
                    total_attempts_used INTEGER DEFAULT 0,
                    total_purchased INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT,
                    last_purchase TEXT
                )
                ''')
                
                # Таблица настроек (для хранения цены)
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Устанавливаем цену по умолчанию, если её нет
                cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) 
                VALUES ('attempts_price', '100')
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def _get_connection(self):
        """Возвращает соединение с базой данных"""
        return sqlite3.connect(self.db_name)

    def get_user_attempts(self, user_id: int) -> int:
        """Получение количества оставшихся попыток пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT attempts FROM users WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    # Создаем нового пользователя с 1 попыткой
                    cursor.execute('''
                    INSERT INTO users (user_id, attempts) VALUES (?, 1)
                    ''', (user_id,))
                    conn.commit()
                    return 1
        except Exception as e:
            logger.error(f"Error in get_user_attempts: {str(e)}")
            return 0

    def decrease_attempts(self, user_id: int) -> int:
        """Уменьшение количества попыток"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем текущее количество попыток
                cursor.execute('''
                SELECT attempts, total_attempts_used FROM users WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()
                
                if result:
                    attempts, total_used = result
                    if attempts > 0:
                        new_attempts = attempts - 1
                        cursor.execute('''
                        UPDATE users 
                        SET attempts = ?, 
                            total_attempts_used = ?,
                            last_used = ?
                        WHERE user_id = ?
                        ''', (new_attempts, total_used + 1, datetime.now().isoformat(), user_id))
                        conn.commit()
                        return new_attempts
                return 0
        except Exception as e:
            logger.error(f"Error in decrease_attempts: {str(e)}")
            return 0

    def add_attempts(self, user_id: int, amount: int = 10):
        """Добавление попыток после оплаты"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем текущие значения
                cursor.execute('''
                SELECT attempts, total_purchased FROM users WHERE user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()
                
                current_attempts = result[0] if result else 0
                total_purchased = result[1] if result else 0
                
                # Обновляем или создаем запись
                cursor.execute('''
                INSERT INTO users (user_id, attempts, total_purchased, last_purchase)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    attempts = attempts + ?,
                    total_purchased = total_purchased + ?,
                    last_purchase = ?,
                    updated_at = ?
                ''', (
                    user_id, 
                    current_attempts + amount, 
                    total_purchased + amount,
                    datetime.now().isoformat(),
                    amount,
                    amount,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error in add_attempts: {str(e)}")
            raise

    def get_price(self) -> float:
        """Получает текущую цену за 10 попыток"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT value FROM settings WHERE key = 'attempts_price'
                ''')
                result = cursor.fetchone()
                return float(result[0]) if result else 100.0
        except Exception as e:
            logger.error(f"Error getting price: {str(e)}")
            return 100.0

    def update_price(self, new_price: float) -> bool:
        """Обновляет цену за 10 попыток"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ''', ('attempts_price', str(new_price), datetime.now().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating price: {str(e)}")
            return False