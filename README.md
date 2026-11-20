# 🎮 GAME ZONE

Веб-сайт игрового клуба с системой бронирования и Telegram-ботом для приёма заявок.

## 📌 О проекте

GAME ZONE — информационная система игрового клуба, позволяющая пользователям просматривать услуги клуба, регистрироваться, бронировать игровые места и взаимодействовать с администрацией через Telegram.

## 🛠 Используемые технологии

### Frontend
- HTML5
- CSS3
- JavaScript
- Nginx

### Backend
- Python
- Flask
- SQLite
- SQLAlchemy
- Flask-Login
- Flask-WTF

### Telegram
- Telegram Bot API
- aiogram 3
- Python

### Инфраструктура
- Ubuntu Server
- Docker
- Docker Compose
- Docker Volumes
- Cron

## 📂 Структура проекта

```text
game-zone/
├── site/
│   ├── images/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── auth.html
│   ├── auth.css
│   ├── auth.js
│   ├── account.html
│   ├── account.css
│   ├── account.js
│   ├── booking.html
│   ├── booking.css
│   ├── booking.js
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── backend/
│   └── Flask backend
│
├── bot/
│   ├── bot.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── backups/
│   └── резервные копии SQLite
│
├── docker-compose.yml
├── backup.sh
├── deploy.sh
└── README.md
```

## 🚀 Запуск проекта

Для запуска необходимы:
- Ubuntu Server;
- установленный Docker;
- Docker Compose;
- настроенный файл `bot/.env`.

### 1. Настройка Telegram-бота

Создать файл `bot/.env`:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
OWNER_ID=YOUR_TELEGRAM_ID
```

Не публикуйте этот файл и не добавляйте его в Git.

### 2. Запуск контейнеров

Из корневой папки проекта:

```bash
docker compose up -d --build
```

### 3. Проверка состояния

```bash
docker compose ps
```

### 4. Просмотр логов

Сайт:

```bash
docker compose logs -f website
```

Telegram-бот:

```bash
docker compose logs -f bot
```

## 💾 Резервное копирование

Для создания резервной копии базы данных:

```bash
./backup.sh
```

Копии сохраняются в папке `backups/`.

Автоматическое резервное копирование настроено через Cron ежедневно в 03:00 UTC.

## 🔄 Обновление проекта

Для пересборки и запуска проекта:

```bash
./deploy.sh
```

Скрипт создаёт резервную копию, пересобирает Docker-контейнеры и проверяет их состояние.

## 🐳 Docker

Проект использует два основных контейнера:

| Контейнер | Назначение |
|---|---|
| game-zone-website | Веб-сайт на Nginx |
| game-zone-bot | Telegram-бот |

Порт сайта: `8200`.

Telegram-бот использует Long Polling и не требует отдельного публичного порта.

База данных заявок бота хранится в Docker Volume `game-zone_bot_data`.

## 🔐 Безопасность

- Токен Telegram хранится в `.env`.
- Файл `.env` исключён из Git.
- Доступ к `.env` ограничен правами файловой системы.
- База данных бота хранится в Docker Volume.
- Предусмотрено резервное копирование SQLite.

## 📱 Telegram

Бот проекта: [@GameZoneSitebot](https://t.me/GameZoneSitebot)

## 👨‍💻 Автор проекта

GAME ZONE — учебный проект по разработке и развёртыванию веб-приложений с использованием Docker и Telegram Bot API.
