from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)

    telegram_id = db.Column(db.BigInteger, unique=True, nullable=True)
    telegram_link_code_hash = db.Column(db.String(64), nullable=True)
    telegram_link_expires_at = db.Column(db.DateTime, nullable=True)

    bookings = db.relationship("Booking", backref="user", lazy=True)


class GamingPlace(db.Model):
    __tablename__ = "gaming_places"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    place_type = db.Column(db.String(30), nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey("gaming_places.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, nullable=True)
class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    event_type = db.Column(
        db.String(30),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False
    )

    booking_id = db.Column(
        db.Integer,
        nullable=True
    )

    place_name = db.Column(
        db.String(100),
        nullable=True
    )

    booking_date = db.Column(
        db.String(10),
        nullable=True
    )

    start_time = db.Column(
        db.String(5),
        nullable=True
    )

    end_time = db.Column(
        db.String(5),
        nullable=True
    )