# Базовый образ
FROM python:3.11-slim

# Порт для Timeweb Cloud
EXPOSE 3000

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создаем .env файл если его нет
RUN touch .env

# Команда запуска
CMD gunicorn --bind 0.0.0.0:3000 app:app --workers 1 --timeout 120