from flask_apscheduler import APScheduler
from models import db, Alarm
from datetime import datetime, timedelta

scheduler = APScheduler()

active_jobs = {}


def trigger_alarm(alarm_id):
    alarm = Alarm.query.get(alarm_id)
    if not alarm:
        return

    # The browser polls `/alarms` and triggers UI sound when matched
    print("Alarm triggered:", alarm_id)

    if not alarm.repeat_daily:
        db.session.delete(alarm)
        db.session.commit()


def schedule_alarm_jobs():
    global active_jobs

    # clear jobs
    for job_id in list(active_jobs.keys()):
        scheduler.remove_job(job_id)

    active_jobs = {}

    alarms = Alarm.query.all()

    for alarm in alarms:
        job_id = f"alarm_{alarm.id}"

        alarm_dt = datetime.fromisoformat(alarm.time)

        scheduler.add_job(
            id=job_id,
            func=trigger_alarm,
            args=[alarm.id],
            trigger="date",
            run_date=alarm_dt
        )

        active_jobs[job_id] = alarm.id
