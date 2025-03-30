# Базовый образ для сборки
FROM python:3.11-slim as builder

WORKDIR /app

# Установка системных зависимостей для Firebase Admin
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости из builder
COPY --from=builder /root/.local /root/.local

# Копируем файлы проекта
COPY . .

# Переменные окружения
ENV PATH=/root/.local/bin:$PATH
ENV WEBHOOK_ENABLED=true
ENV PORT=3000

# Запуск через gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]