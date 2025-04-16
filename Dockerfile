# Указываем базовый образ
FROM python:3.11-slim

# Явно указываем порт для Timeweb Cloud
EXPOSE 3000/tcp

# Устанавливаем рабочую директорию
WORKDIR /app

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем сначала requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Создаем .env файл если его нет
RUN touch .env

# Запуск приложения через gunicorn
ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:3000", "app:app", "--workers", "1", "--timeout", "120"]