# mini-app-tg-exchanger — Telegram WebApp для обмена валют
![Фото](https://github.com/kripersi/mini-app-tg-exchanger/blob/main/screenshots/img.png)
![Фото](https://github.com/kripersi/mini-app-tg-exchanger/blob/main/screenshots/img_1.png)

mini-app-tg-exchanger — это современное веб-приложение, встроенное в Telegram, которое позволяет пользователям удобно и безопасно оформлять заявки на обмен валют. Поддерживаются криптовалюты, фиатные валюты и локальные города, с автоматическим расчётом курсов и проверкой лимитов.

## 🚀 Возможности

- Выбор страны и города с автозагрузкой доступных валют
- Поддержка обмена между криптовалютами и фиатом 
- Автоматический расчёт курса с учётом комиссии
- Проверка лимитов в эквиваленте USDT
- Валидация даты и времени визита
- Уведомление администраторов через Telegram-бота
- Интеграция с Telegram WebApp API 
- API для получения информации о странах и курсах
- Реферальная программа
- Блокирование пользователей в админке

## 🧩 Технологии

- Backend: Flask + SQLAlchemy
- Frontend: HTML, CSS, JavaScript
- Telegram WebApp API
- PostgreSQL
- CCXT, yFinance, MOEX ISS API
- Отправка уведомлений через Telegram-бота

## ⚙️ Установка и запуск

1. Клонируй репозиторий:
```bash
   git clone https://github.com/kripersi/mini-app-tg-exchanger.git
```

2. Установи зависимости:
```bash
   pip install -r requirements.txt
```

3. Скачай ngrok(для тестов):
```bash
https://ngrok.com/
```

4. Получи ссылку в ngrok и вставь в config.py
```bash
URL_SITE = "https://URL_SITE"
```

5. Запусти сервер:
```bash
   python main.py
```
## 📡 API

- GET /api/country/<name> — получить список валют и городов по стране
- GET /get_rate?give_currency=BTC&get_currency=USDT — получить лучший курс обмена
- GET /api/history/<user_id> — получение истории заявок пользователя
- GET /api/referral_link/<user_id> — генерация реферальной ссылки для Telegram WebApp
- GET /api/referral/<user_id> — получение информации о приглашённых пользователем
- GET /api/user/<tg_id> — получение данных пользователя по Telegram ID
- GET /api/is_admin/<user_id> — проверка, является ли пользователь администратором

## 🛡️ Валидация и безопасность

- Все поля формы валидируются как на клиенте, так и на сервере
- Проверка лимитов через пересчёт в USDT
- Защита от некорректных дат, одинаковых валют и пустых полей
- Уведомления админов об успешной заявке
- Возможность заблокировать\разблокировать пользователя в админке

## 📬 Обратная связь

Если у вас есть предложения, баг-репорты или идеи — создайте issue или напишите мне в Telegram: @Marpexiz


## Другие фото
![Фото](https://github.com/kripersi/mini-app-tg-exchanger/blob/main/screenshots/img_2.png)
![Фото](https://github.com/kripersi/mini-app-tg-exchanger/blob/main/screenshots/img_3.png)
![Фото](https://github.com/kripersi/mini-app-tg-exchanger/blob/main/screenshots/img_4.png)
![Админка](https://github.com/kripersi/mini-app-tg-exchanger/blob/main/screenshots/img_5.png)
