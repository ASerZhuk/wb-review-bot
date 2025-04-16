FROM python:3.8-slim

WORKDIR /app

# Копируем зависимости для установки
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Переменные окружения будут загружены из .env файла через python-dotenv

# Указываем порт, который будет прослушивать приложение
EXPOSE 80

# Команда для запуска приложения
CMD ["gunicorn", "--bind", "0.0.0.0:80", "main:app"] 