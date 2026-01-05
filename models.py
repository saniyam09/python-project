from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))


class Alarm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    time = db.Column(db.String(32))   # ISO datetime string
    repeat_daily = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=False)
    label = db.Column(db.String(100), default="Alarm")
    sound = db.Column(db.String(100), default="alarm.mp3")
    snooze_duration = db.Column(db.Integer, default=5)  # minutes
    weekdays = db.Column(db.String(20), default="")  # e.g., "1,2,3,4,5" for Mon-Fri


def init_db():
    db.create_all()
