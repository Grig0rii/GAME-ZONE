import asyncio
import os
import sqlite3
import logging

import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters.command import CommandObject
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:5000"
)

if not BOT_TOKEN or not OWNER_ID:
    raise RuntimeError("Не настроены BOT_TOKEN или OWNER_ID")

if not INTERNAL_API_KEY:
    raise RuntimeError("Не настроен INTERNAL_API_KEY")

OWNER_ID = int(OWNER_ID)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_PATH = "/app/data/requests.db"

os.makedirs("/app/data", exist_ok=True)

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🖥 Компьютеры")],
        [KeyboardButton(text="🎮 PlayStation")],
        [KeyboardButton(text="🏆 Турниры")],
        [KeyboardButton(text="📜 История действий")]
    ],
    resize_keyboard=True
)

confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Отправить заявку")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

user_requests = {}


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username TEXT,
                activity TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


async def backend_request(method, path, data=None):
    headers = {
        "X-Internal-API-Key": INTERNAL_API_KEY
    }

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        async with session.request(
            method,
            f"{BACKEND_URL}{path}",
            headers=headers,
            json=data
        ) as response:

            result = await response.json(
                content_type=None
            )

            return response.status, result


async def get_linked_user(telegram_id):
    try:
        status, data = await backend_request(
            "GET",
            f"/internal/telegram/user/{telegram_id}"
        )

        if status == 200 and data.get("linked"):
            return data

        return None

    except Exception:
        logging.exception(
            "Ошибка проверки Telegram-пользователя"
        )
        return None


async def require_linked(message):
    user = await get_linked_user(message.from_user.id)

    if not user:
        await message.answer(
            "🔐 Чтобы пользоваться ботом, сначала привяжи "
            "Telegram к аккаунту GAME ZONE.\n\n"
            "1. Войди в аккаунт на сайте.\n"
            "2. Получи код привязки в личном кабинете.\n"
            "3. Отправь боту команду:\n\n"
            "/link ТВОЙ_КОД"
        )

        return False

    return True


@dp.message(CommandStart())
async def start(message: Message):

    linked_user = await get_linked_user(
        message.from_user.id
    )

    if not linked_user:
        await message.answer(
            "Добро пожаловать в GAME ZONE! 🎮\n\n"
            "Для начала привяжи Telegram к аккаунту сайта.\n\n"
            "Получи код в личном кабинете и отправь:\n"
            "/link ТВОЙ_КОД"
        )
        return

    await message.answer(
        f"Привет, {linked_user['full_name']}! 🎮\n\n"
        "Твой аккаунт GAME ZONE подключён.\n"
        "Выбирай услугу:",
        reply_markup=keyboard
    )


@dp.message(Command("link"))
async def link_account(
    message: Message,
    command: CommandObject
):

    code = command.args

    if not code:
        await message.answer(
            "Укажи код привязки:\n\n"
            "/link ТВОЙ_КОД"
        )
        return

    if len(code.strip()) > 100:
        await message.answer("Некорректный код.")
        return

    try:
        status, data = await backend_request(
            "POST",
            "/internal/telegram/link",
            {
                "code": code.strip(),
                "telegram_id": message.from_user.id
            }
        )

        if status == 200:
            await message.answer(
                "✅ Telegram успешно привязан!\n\n"
                f"Аккаунт: {data.get('username')}\n\n"
                "Теперь можешь пользоваться ботом.",
                reply_markup=keyboard
            )

        else:
            await message.answer(
                "❌ Не удалось привязать аккаунт.\n\n"
                + data.get(
                    "error",
                    "Проверь код и попробуй снова."
                )
            )

    except Exception:
        logging.exception("Ошибка привязки Telegram")

        await message.answer(
            "⚠️ Не удалось связаться с сервером GAME ZONE. "
            "Попробуй немного позже."
        )


@dp.message(F.text == "📜 История действий")
async def show_history(message: Message):

    if not await require_linked(message):
        return

    await message.answer("⏳ Загружаю историю действий...")

    try:
        status, data = await backend_request(
            "GET",
            f"/internal/telegram/history/{message.from_user.id}"
        )

        if status != 200:
            await message.answer(
                "⚠️ Не удалось загрузить историю. "
                "Попробуй немного позже."
            )
            return

        history = data.get("history", [])

        if not history:
            await message.answer(
                "📜 История действий пока пуста.\n\n"
                "Здесь будут отображаться твои бронирования "
                "и их отмены.",
                reply_markup=keyboard
            )
            return

        messages = []

        for item in history:
            event_type = item.get("event_type")

            if event_type == "booking_created":
                title = "🟢 Бронирование создано"
            elif event_type == "booking_cancelled":
                title = "🔴 Бронирование отменено"
            else:
                title = "📌 Действие в аккаунте"

            lines = [
                title,
                f"Время события: {item.get('created_at') or 'не указано'}"
            ]

            if item.get("place_name"):
                lines.append(
                    f"Место: {item['place_name']}"
                )

            if item.get("booking_date"):
                lines.append(
                    f"Дата бронирования: {item['booking_date']}"
                )

            if item.get("start_time") or item.get("end_time"):
                start = item.get("start_time") or "?"
                end = item.get("end_time") or "?"

                lines.append(
                    f"Время бронирования: {start}–{end}"
                )

            messages.append("\n".join(lines))

        # Отправляем небольшими частями,
        # чтобы не превышать лимит Telegram.
        text = "📜 ТВОЯ ИСТОРИЯ ДЕЙСТВИЙ\n\n"

        for entry in messages:
            if len(text) + len(entry) + 3 > 3500:
                await message.answer(text)
                text = ""

            text += entry + "\n\n"

        if text:
            await message.answer(
                text,
                reply_markup=keyboard
            )

    except Exception:
        logging.exception("Ошибка загрузки истории")

        await message.answer(
            "⚠️ Не удалось связаться с сервером. "
            "Попробуй позже.",
            reply_markup=keyboard
        )


@dp.message(F.text.in_({
    "🖥 Компьютеры",
    "🎮 PlayStation",
    "🏆 Турниры"
}))
async def choose_activity(message: Message):

    if not await require_linked(message):
        return

    user_requests[message.from_user.id] = message.text

    await message.answer(
        f"Ты выбрал: {message.text}\n\n"
        "Подтверди отправку заявки.",
        reply_markup=confirm_keyboard
    )


@dp.message(F.text == "✅ Отправить заявку")
async def confirm_request(message: Message):

    if not await require_linked(message):
        return

    user_id = message.from_user.id
    activity = user_requests.get(user_id)

    if not activity:
        await message.answer(
            "Сначала выбери услугу.",
            reply_markup=keyboard
        )
        return

    username = message.from_user.username or "не указан"

    with sqlite3.connect(DB_PATH) as conn:

        cursor = conn.execute(
            """
            INSERT INTO requests (
                telegram_id,
                username,
                activity
            )
            VALUES (?, ?, ?)
            """,
            (user_id, username, activity)
        )

        request_id = cursor.lastrowid

    await message.answer(
        f"✅ Заявка №{request_id} отправлена!\n"
        "Администратор скоро свяжется с тобой.",
        reply_markup=keyboard
    )

    try:
        await bot.send_message(
            OWNER_ID,
            f"📩 Новая заявка №{request_id}\n\n"
            f"Услуга: {activity}\n"
            f"Пользователь: @{username}\n"
            f"Telegram ID: {user_id}"
        )

    except Exception:
        logging.exception(
            "Не удалось отправить уведомление владельцу"
        )

    user_requests.pop(user_id, None)


@dp.message(F.text == "❌ Отмена")
async def cancel_request(message: Message):

    user_requests.pop(message.from_user.id, None)

    await message.answer(
        "Заявка отменена. Можешь выбрать другую услугу.",
        reply_markup=keyboard
    )


async def main():

    init_db()

    logging.info("GAME ZONE bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())