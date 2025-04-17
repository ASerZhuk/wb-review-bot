FROM python:3.10

WORKDIR /app

# Копируем зависимости для установки
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем код приложения
COPY . .

# Переменные окружения будут загружены из .env файла через python-dotenv

# Указываем порт, который будет прослушивать приложение
EXPOSE 8080

# Команда для запуска приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"] 