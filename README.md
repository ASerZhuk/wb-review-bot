# Wildberries Review Analysis Bot

Telegram бот для анализа отзывов с Wildberries с использованием AI.

## Особенности

- Анализ отзывов с Wildberries по ссылке или артикулу
- Вывод основных плюсов и минусов товара
- Система оплаты через ЮMoney
- Подсчет использованных попыток через Firebase

## Настройка окружения

1. Клонируйте репозиторий:

```
git clone https://github.com/your-username/wb-review-bot.git
cd wb-review-bot
```

2. Создайте виртуальное окружение и установите зависимости:

```
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate  # Для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `example.env` и заполните его своими значениями:

```
cp example.env .env
```

4. Настройка Firebase:

   - Создайте проект в [Firebase Console](https://console.firebase.google.com/)
   - Создайте сервисный аккаунт и скачайте JSON-файл с учетными данными
   - Переименуйте файл в `serviceAccountKey.json` и поместите его в корневую директорию проекта

5. Настройка Telegram бота:
   - Создайте бота через [@BotFather](https://t.me/BotFather) и получите токен
   - Добавьте токен в файл `.env`

## Запуск

### Локальный запуск для разработки:

```
python app.py
```

### Запуск через webhook:

Убедитесь, что в `.env` установлен `WEBHOOK_ENABLED=true`

```
python app.py
```

## Размещение на Render

1. Создайте новый Web Service на [Render](https://render.com/)
2. Подключите свой Git-репозиторий
3. Добавьте все переменные окружения из `.env` в настройках Render
4. Укажите команду запуска: `gunicorn app:app`
5. Добавьте `gunicorn` в зависимости (`requirements.txt`)

## Настройка администраторов

Администраторы могут использовать команду `/admin` для доступа к панели управления.
ID администраторов нужно добавить в список `ADMIN_IDS` в файле `bot.py`.
