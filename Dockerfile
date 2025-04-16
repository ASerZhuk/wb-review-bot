FROM python:3.8-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Сделаем health.py исполняемым
RUN chmod +x health.py

# Открываем порт
EXPOSE 8080

# Запуск через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]