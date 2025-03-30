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

# Копируем файлы проекта и сертификат Firebase
COPY . .
COPY paymentbotwb-firebase-adminsdk-fbsvc-3ad5a24c65.json .

# Переменные окружения
ENV PATH=/root/.local/bin:$PATH
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/paymentbotwb-firebase-adminsdk-fbsvc-3ad5a24c65.json"

# Проверяем наличие файла сертификата
RUN if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then \
    echo "ERROR: Firebase credentials file not found!" && exit 1; \
    fi

# Запуск приложения
CMD ["python", "bot.py"]