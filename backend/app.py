import os
import secrets
import hashlib
import hmac

from functools import wraps
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


from flask import Flask, request, jsonify
from flask_cors import CORS

from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import db, User, GamingPlace, Booking, ActivityLog
load_dotenv()

# ==================================================
# НАСТРОЙКИ
# ==================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-secret"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

CORS(
    app,
    origins=["http://89.127.206.24:8200"],
    supports_credentials=True
)

db.init_app(app)


# ==================================================
# ЧАСОВОЙ ПОЯС И ВНУТРЕННИЙ API
# ==================================================

CLUB_TIMEZONE = ZoneInfo("Europe/Madrid")

INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")


def get_club_time():
    return datetime.now(CLUB_TIMEZONE)


def require_internal_api_key(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not INTERNAL_API_KEY:
            return jsonify({
                "error": "Internal API is not configured"
            }), 503

        provided_key = request.headers.get(
            "X-Internal-API-Key",
            ""
        )

        if not hmac.compare_digest(
            provided_key,
            INTERNAL_API_KEY
        ):
            return jsonify({
                "error": "Unauthorized"
            }), 401

        return func(*args, **kwargs)

    return wrapper


# ==================================================
# АВТОРИЗАЦИЯ
# ==================================================

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==================================================
# ГЛАВНАЯ СТРАНИЦА BACKEND
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "GAME ZONE backend работает!",
        "status": "OK"
    })


# ==================================================
# РЕГИСТРАЦИЯ
# ==================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")
    password_confirm = data.get("password_confirm", "")
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip() or None
    email = data.get("email", "").strip().lower() or None

    if not username or not password or not full_name:
        return jsonify({
            "error": "Заполни обязательные поля"
        }), 400

    if not password_confirm:
        return jsonify({
            "error": "Подтверди пароль"
        }), 400

    if len(username) < 3 or len(username) > 50:
        return jsonify({
            "error": "Логин должен содержать от 3 до 50 символов"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Пароль должен содержать минимум 8 символов"
        }), 400

    if password != password_confirm:
        return jsonify({
            "error": "Пароли не совпадают"
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            "error": "Такой логин уже существует"
        }), 409

    if email and User.query.filter_by(email=email).first():
        return jsonify({
            "error": "Этот email уже зарегистрирован"
        }), 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        phone=phone,
        email=email
    )

    db.session.add(user)
    db.session.commit()

    login_user(user)

    return jsonify({
        "message": "Регистрация прошла успешно",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name
        }
    }), 201


# ==================================================
# ВХОД В АККАУНТ
# ==================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "error": "Введи логин и пароль"
        }), 400

    user = User.query.filter_by(
        username=username
    ).first()

    if not user or not check_password_hash(
        user.password_hash,
        password
    ):
        return jsonify({
            "error": "Неверный логин или пароль"
        }), 401

    login_user(user)

    return jsonify({
        "message": "Вход выполнен успешно",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name
        }
    }), 200


# ==================================================
# СОЗДАНИЕ КОДА ПРИВЯЗКИ TELEGRAM
# ==================================================

@app.route("/api/telegram/link-code", methods=["POST"])
@login_required
def create_telegram_link_code():

    user = db.session.get(User, current_user.id)

    if user.telegram_id:
        return jsonify({
            "error": "Telegram уже привязан"
        }), 409

    code = secrets.token_urlsafe(6)

    code_hash = hashlib.sha256(
        code.encode()
    ).hexdigest()

    user.telegram_link_code_hash = code_hash

    user.telegram_link_expires_at = (
        datetime.utcnow() + timedelta(minutes=10)
    )

    db.session.commit()

    return jsonify({
        "code": code,
        "expires_in": 600,
        "bot_url": "https://t.me/GameZoneSitebot"
    }), 200


# ==================================================
# ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ
# ==================================================

@app.route("/api/me", methods=["GET"])
@login_required
def get_current_user():

    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "email": current_user.email,
        "telegram_linked": bool(current_user.telegram_id)
    })


# ==================================================
# ВЫХОД ИЗ АККАУНТА
# ==================================================

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():

    logout_user()

    return jsonify({
        "message": "Выход выполнен успешно"
    })


# ==================================================
# СПИСОК ИГРОВЫХ МЕСТ
# ==================================================

@app.route("/api/places", methods=["GET"])
def get_places():

    places = GamingPlace.query.filter_by(
        is_active=True
    ).all()

    result = []

    for place in places:

        result.append({
            "id": place.id,
            "name": place.name,
            "type": place.place_type
        })

    return jsonify(result)


# ==================================================
# ПРИВЯЗКА TELEGRAM ЧЕРЕЗ БОТА
# ==================================================

@app.route("/internal/telegram/link", methods=["POST"])
@require_internal_api_key
def internal_telegram_link():

    data = request.get_json(silent=True) or {}

    code = data.get("code", "")
    telegram_id = data.get("telegram_id")

    if not isinstance(code, str) or not code or len(code) > 100:
        return jsonify({
            "error": "Некорректный код"
        }), 400

    try:

        telegram_id = int(telegram_id)

        if telegram_id <= 0:
            raise ValueError

    except (ValueError, TypeError):

        return jsonify({
            "error": "Некорректный Telegram ID"
        }), 400

    code_hash = hashlib.sha256(
        code.encode()
    ).hexdigest()

    user = User.query.filter_by(
        telegram_link_code_hash=code_hash
    ).first()

    if not user:

        return jsonify({
            "error": "Код недействителен или уже использован"
        }), 404

    if not user.telegram_link_expires_at:

        return jsonify({
            "error": "Код недействителен"
        }), 400

    if user.telegram_link_expires_at < datetime.utcnow():

        user.telegram_link_code_hash = None
        user.telegram_link_expires_at = None

        db.session.commit()

        return jsonify({
            "error": "Срок действия кода истёк"
        }), 400

    if user.telegram_id:

        return jsonify({
            "error": "К аккаунту уже привязан Telegram"
        }), 409

    existing_user = User.query.filter_by(
        telegram_id=telegram_id
    ).first()

    if existing_user:

        return jsonify({
            "error": "Этот Telegram уже привязан к другому аккаунту"
        }), 409

    user.telegram_id = telegram_id

    user.telegram_link_code_hash = None
    user.telegram_link_expires_at = None

    db.session.commit()

    return jsonify({
        "message": "Telegram успешно привязан",
        "username": user.username
    }), 200


# ==================================================
# ПРОВЕРКА TELEGRAM-ПОЛЬЗОВАТЕЛЯ
# ==================================================

@app.route(
    "/internal/telegram/user/<int:telegram_id>",
    methods=["GET"]
)
@require_internal_api_key
def telegram_get_user(telegram_id):
    user = User.query.filter_by(
        telegram_id=telegram_id
    ).first()

    if not user:
        return jsonify({
            "linked": False,
            "error": "Аккаунт не привязан"
        }), 404

    return jsonify({
        "linked": True,
        "username": user.username,
        "full_name": user.full_name
    }), 200


@app.route(
    "/internal/telegram/history/<int:telegram_id>",
    methods=["GET"]
)
@require_internal_api_key
def telegram_user_history(telegram_id):
    user = User.query.filter_by(
        telegram_id=telegram_id
    ).first()

    if not user:
        return jsonify({
            "error": "Аккаунт не привязан"
        }), 404

    logs = (
        ActivityLog.query
        .filter_by(user_id=user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(30)
        .all()
    )

    history = []

    for log in logs:
        history.append({
            "event_type": log.event_type,
            "created_at": log.created_at.strftime(
                "%d.%m.%Y %H:%M"
            ),
            "place_name": log.place_name,
            "booking_date": log.booking_date,
            "start_time": log.start_time,
            "end_time": log.end_time
        })

    return jsonify({
        "username": user.username,
        "history": history
    }), 200
    # ==================================================
# УВЕДОМЛЕНИЯ ДЛЯ АДМИНСКОГО TELEGRAM-БОТА
# ==================================================

@app.route("/internal/notifications", methods=["GET"])
@require_internal_api_key
def internal_notifications():

    after_id = request.args.get("after_id", type=int)

    latest_id = (
        db.session.query(db.func.max(ActivityLog.id)).scalar()
        or 0
    )

    # Первый запуск: сообщаем боту текущую позицию,
    # чтобы не отправлять старые события.
    if after_id is None or after_id < 0:
        return jsonify({
            "events": [],
            "latest_id": latest_id
        }), 200

    logs = (
        ActivityLog.query
        .filter(
            ActivityLog.id > after_id,
            ActivityLog.event_type.in_([
                "booking_created",
                "booking_cancelled"
            ])
        )
        .order_by(ActivityLog.id.asc())
        .limit(100)
        .all()
    )

    events = []

    for log in logs:

        user = db.session.get(User, log.user_id)

        events.append({
            "id": log.id,
            "event_type": log.event_type,
            "username": user.username if user else "Неизвестно",
            "full_name": user.full_name if user else "Неизвестно",
            "place_name": log.place_name,
            "booking_date": log.booking_date,
            "start_time": log.start_time,
            "end_time": log.end_time
        })

    return jsonify({
        "events": events,
        "latest_id": latest_id
    }), 200
# ==================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОТМЕНЫ
# ==================================================

def get_cancellation_info(booking, now=None):

    if now is None:
        now = get_club_time()

    if not booking.created_at:

        return {
            "allowed": False,
            "reason": "Не удалось определить время создания брони",
            "deadline": None
        }

    try:

        booking_datetime = datetime.strptime(
            f"{booking.date} {booking.start_time}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=CLUB_TIMEZONE)

    except ValueError:

        return {
            "allowed": False,
            "reason": "Некорректная дата бронирования",
            "deadline": None
        }

    created_at = booking.created_at

    if created_at.tzinfo is None:

        created_at = created_at.replace(
            tzinfo=CLUB_TIMEZONE
        )

    else:

        created_at = created_at.astimezone(
            CLUB_TIMEZONE
        )

    time_until_game = booking_datetime - now
    time_since_creation = now - created_at

    if time_until_game <= timedelta(0):

        return {
            "allowed": False,
            "reason": "Игра уже началась или завершилась",
            "deadline": None
        }

    booking_was_far_ahead = (
        booking_datetime - created_at > timedelta(days=7)
    )

    if booking_was_far_ahead:

        deadline = booking_datetime - timedelta(days=2)

        allowed = time_until_game > timedelta(days=2)

        reason = (
            "Отмена разрешена до момента, "
            "когда до игры останется 48 часов"
        )

    else:

        deadline = created_at + timedelta(days=2)

        allowed = (
            time_since_creation <= timedelta(days=2)
        )

        reason = (
            "Отмена разрешена только в первые "
            "48 часов после создания бронирования"
        )

    return {
        "allowed": allowed,
        "reason": reason,
        "deadline": deadline.isoformat()
    }


# ==================================================
# СОЗДАНИЕ БРОНИРОВАНИЯ
# ==================================================

@app.route("/api/bookings", methods=["POST"])
@login_required
def create_booking():

    data = request.get_json(silent=True) or {}

    place_id = data.get("place_id")
    booking_date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not all([
        place_id,
        booking_date,
        start_time,
        end_time
    ]):

        return jsonify({
            "error": "Заполни все поля бронирования"
        }), 400

    try:

        place_id = int(place_id)

        booking_day = datetime.strptime(
            booking_date,
            "%Y-%m-%d"
        ).date()

        start = datetime.strptime(
            start_time,
            "%H:%M"
        ).time()

        end = datetime.strptime(
            end_time,
            "%H:%M"
        ).time()

    except (ValueError, TypeError):

        return jsonify({
            "error": "Неверный формат даты или времени"
        }), 400

    now = get_club_time()

    if booking_day < now.date():

        return jsonify({
            "error": "Нельзя забронировать прошедшую дату"
        }), 400

    if end <= start:

        return jsonify({
            "error": "Время окончания должно быть позже начала"
        }), 400

    booking_datetime = datetime.combine(
        booking_day,
        start,
        tzinfo=CLUB_TIMEZONE
    )

    if booking_datetime <= now:

        return jsonify({
            "error": "Нельзя забронировать прошедшее время"
        }), 400

    place = db.session.get(
        GamingPlace,
        place_id
    )

    if not place or not place.is_active:

        return jsonify({
            "error": "Игровое место недоступно"
        }), 404

    existing_booking = Booking.query.filter(
        Booking.place_id == place_id,
        Booking.date == booking_date,
        Booking.status == "active",
        Booking.start_time < end_time,
        Booking.end_time > start_time
    ).first()

    if existing_booking:

        return jsonify({
            "error": "Это место уже забронировано на выбранное время"
        }), 409

    booking = Booking(
        user_id=current_user.id,
        place_id=place_id,
        date=booking_date,
        start_time=start_time,
        end_time=end_time,
        status="active",
        created_at=now.replace(tzinfo=None)
    )

    db.session.add(booking)
    db.session.flush()

    activity = ActivityLog(
        user_id=current_user.id,
        event_type="booking_created",
        created_at=now.replace(tzinfo=None),
        booking_id=booking.id,
        place_name=place.name,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time
    )

    db.session.add(activity)
    db.session.commit()

    return jsonify({
        "message": "Бронирование успешно создано",
        "booking_id": booking.id
    }), 201


# ==================================================
# ПРОСМОТР БРОНИРОВАНИЙ
# ==================================================

@app.route("/api/bookings", methods=["GET"])
@login_required
def get_bookings():

    bookings = Booking.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Booking.date,
        Booking.start_time
    ).all()

    result = []

    now = get_club_time()

    for booking in bookings:

        place = db.session.get(
            GamingPlace,
            booking.place_id
        )

        cancellation = get_cancellation_info(
            booking,
            now
        )

        result.append({
            "id": booking.id,
            "place": place.name if place else "Неизвестное место",
            "place_id": booking.place_id,
            "date": booking.date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status,
            "cancel_allowed": (
                cancellation["allowed"]
                if booking.status == "active"
                else False
            ),
            "cancel_reason": cancellation["reason"],
            "cancel_deadline": cancellation["deadline"]
        })

    return jsonify(result)


# ==================================================
# ОТМЕНА БРОНИРОВАНИЯ
# ==================================================

@app.route(
    "/api/bookings/<int:booking_id>/cancel",
    methods=["POST"]
)
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=current_user.id
    ).first()

    if not booking:
        return jsonify({
            "error": "Бронирование не найдено"
        }), 404

    if booking.status != "active":
        return jsonify({
            "error": "Это бронирование уже отменено"
        }), 400

    cancellation = get_cancellation_info(booking)

    if not cancellation["allowed"]:
        return jsonify({
            "error": cancellation["reason"]
        }), 400

    place = db.session.get(
        GamingPlace,
        booking.place_id
    )

    place_name = place.name if place else "Неизвестное место"

    try:
        booking.status = "cancelled"

        activity = ActivityLog(
            user_id=current_user.id,
            event_type="booking_cancelled",
            created_at=get_club_time().replace(tzinfo=None),
            booking_id=booking.id,
            place_name=place_name,
            booking_date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time
        )

        db.session.add(activity)
        db.session.commit()

        return jsonify({
            "message": "Бронирование успешно отменено"
        }), 200

    except Exception:
        db.session.rollback()
        app.logger.exception("Ошибка отмены бронирования")

        return jsonify({
            "error": "Не удалось отменить бронирование"
        }), 500


# ==================================================
# СОЗДАНИЕ И ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ
# ==================================================

with app.app_context():

    db.create_all()

    inspector = db.inspect(db.engine)

    user_columns = [
        column["name"]
        for column in inspector.get_columns("users")
    ]

    if "telegram_id" not in user_columns:

        db.session.execute(
            db.text(
                "ALTER TABLE users ADD COLUMN telegram_id BIGINT"
            )
        )

    if "telegram_link_code_hash" not in user_columns:

        db.session.execute(
            db.text(
                "ALTER TABLE users "
                "ADD COLUMN telegram_link_code_hash VARCHAR(64)"
            )
        )

    if "telegram_link_expires_at" not in user_columns:

        db.session.execute(
            db.text(
                "ALTER TABLE users "
                "ADD COLUMN telegram_link_expires_at DATETIME"
            )
        )

    db.session.commit()

    columns = db.session.execute(
        db.text("PRAGMA table_info(bookings)")
    ).fetchall()

    column_names = [
        column[1]
        for column in columns
    ]

    if "created_at" not in column_names:

        db.session.execute(
            db.text(
                "ALTER TABLE bookings "
                "ADD COLUMN created_at DATETIME"
            )
        )

        db.session.commit()

    migration_time = get_club_time().replace(
        tzinfo=None
    )

    db.session.execute(
        db.text(
            "UPDATE bookings "
            "SET created_at = :created_at "
            "WHERE created_at IS NULL"
        ),
        {
            "created_at": migration_time
        }
    )

    db.session.commit()

    places = [
        {"name": "PC-01", "place_type": "Компьютер"},
        {"name": "PC-02", "place_type": "Компьютер"},
        {"name": "PC-03", "place_type": "Компьютер"},
        {"name": "PS5-01", "place_type": "PlayStation 5"},
        {"name": "PS5-02", "place_type": "PlayStation 5"},
        {"name": "VIP-01", "place_type": "VIP-зона"}
    ]

    for place_data in places:

        existing_place = GamingPlace.query.filter_by(
            name=place_data["name"]
        ).first()

        if not existing_place:

            db.session.add(
                GamingPlace(
                    name=place_data["name"],
                    place_type=place_data["place_type"],
                    is_active=True
                )
            )

    db.session.commit()

    db.session.execute(
        db.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "ix_users_telegram_id_unique ON users (telegram_id)"
        )
    )

    db.session.commit()


# ==================================================
# ЗАПУСК СЕРВЕРА
# ==================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )