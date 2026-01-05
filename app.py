from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import init_db, db, User, Alarm
from scheduler import scheduler, schedule_alarm_jobs
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "change_this_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    init_db()
    schedule_alarm_jobs()

scheduler.init_app(app)
scheduler.start()


def require_login():
    if "user_id" not in session:
        return redirect("/login")


@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            return render_template("register.html", error="All fields are required.")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return render_template("register.html", error="User already exists.")

        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return render_template("login.html", error="Invalid credentials.")

        session["user_id"] = user.id
        session["username"] = user.username
        return redirect("/dashboard")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    alarms = Alarm.query.filter_by(user_id=session["user_id"]).order_by(Alarm.time).all()
    return render_template("dashboard.html", alarms=alarms)


# CRUD API — ALARMS
@app.route("/alarms", methods=["POST"])
def create_alarm():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    alarm_time = data.get("time")
    repeat_daily = data.get("repeat", False)
    label = data.get("label", "Alarm")
    sound = data.get("sound", "alarm.mp3")
    snooze_duration = data.get("snooze_duration", 5)
    weekdays = data.get("weekdays", "")

    new_alarm = Alarm(
        user_id=session["user_id"],
        time=alarm_time,
        repeat_daily=repeat_daily,
        label=label,
        sound=sound,
        snooze_duration=snooze_duration,
        weekdays=weekdays
    )
    db.session.add(new_alarm)
    db.session.commit()

    schedule_alarm_jobs()

    return jsonify({"message": "Alarm created"}), 201


@app.route("/alarms/<int:alarm_id>", methods=["PUT"])
def update_alarm(alarm_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    alarm = Alarm.query.filter_by(id=alarm_id, user_id=session["user_id"]).first()
    if not alarm:
        return jsonify({"error": "Not found"}), 404

    data = request.json
    alarm.time = data.get("time", alarm.time)
    alarm.repeat_daily = data.get("repeat", alarm.repeat_daily)
    alarm.label = data.get("label", alarm.label)
    alarm.sound = data.get("sound", alarm.sound)
    alarm.snooze_duration = data.get("snooze_duration", alarm.snooze_duration)
    alarm.weekdays = data.get("weekdays", alarm.weekdays)

    db.session.commit()

    schedule_alarm_jobs()
    return jsonify({"message": "Alarm updated"})


@app.route("/alarms/<int:alarm_id>", methods=["DELETE"])
def delete_alarm(alarm_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    alarm = Alarm.query.filter_by(id=alarm_id, user_id=session["user_id"]).first()
    if not alarm:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(alarm)
    db.session.commit()

    schedule_alarm_jobs()
    return jsonify({"message": "Deleted"})


@app.route("/alarms/<int:alarm_id>")
def get_alarm(alarm_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    alarm = Alarm.query.filter_by(id=alarm_id, user_id=session["user_id"]).first()
    if not alarm:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": alarm.id,
        "time": alarm.time,
        "repeat": alarm.repeat_daily,
        "label": alarm.label,
        "sound": alarm.sound,
        "snooze_duration": alarm.snooze_duration,
        "weekdays": alarm.weekdays
    })


@app.route("/alarms")
def get_alarms():
    if "user_id" not in session:
        return jsonify([])

    alarms = Alarm.query.filter_by(user_id=session["user_id"]).all()
    return jsonify([
        {
            "id": a.id,
            "time": a.time,
            "repeat": a.repeat_daily
        } for a in alarms
    ])


if __name__ == "__main__":
    app.run(debug=True)
