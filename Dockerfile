# Базовый образ
FROM python:3.11-slim

# Явно указываем порт для Timeweb Cloud
EXPOSE 3000/tcp

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

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "1", "--timeout", "120", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "app:app"]