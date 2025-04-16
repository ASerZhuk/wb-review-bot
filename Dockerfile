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

# Создаем скрипт для проверки и запуска
RUN echo '#!/bin/bash\n\
    echo "Checking environment variables..."\n\
    required_vars=("BOT_TOKEN" "WEBHOOK_HOST" "FIREBASE_PROJECT_ID" "FIREBASE_PRIVATE_KEY")\n\
    for var in "${required_vars[@]}"; do\n\
    if [ -z "${!var}" ]; then\n\
    echo "Error: Required environment variable $var is not set"\n\
    exit 1\n\
    fi\n\
    done\n\
    echo "Environment variables OK"\n\
    echo "Starting gunicorn..."\n\
    exec gunicorn --bind 0.0.0.0:3000 app:app --workers 1 --timeout 120 --log-level debug\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Команда запуска
CMD ["/app/start.sh"]