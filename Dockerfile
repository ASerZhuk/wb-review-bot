# Базовый образ
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создаем скрипт запуска
RUN echo '#!/bin/bash\n\
    echo "Waiting for system initialization (5s)..."\n\
    sleep 5\n\
    echo "Starting application..."\n\
    exec gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 120 --log-level debug --access-logfile - --error-logfile - app:app' > /app/start.sh && \
    chmod +x /app/start.sh

# Явно указываем порт, который будет прослушивать приложение
EXPOSE 8080

# Запуск приложения
CMD ["/app/start.sh"]