from flask_apscheduler import APScheduler
from models import Alarm
from datetime import datetime

scheduler = APScheduler()

def trigger_alarm(alarm_id):
    alarm = Alarm.query.get(alarm_id)
    if alarm:
        print(f"Alarm triggered: {alarm.time} for user {alarm.user_id}")
        # Here you could add logic to notify the user, e.g., via email, push notification, or play sound if possible
    else:
        print(f"Alarm with id {alarm_id} not found")

def schedule_alarm_jobs():
    scheduler.remove_all_jobs()
    alarms = Alarm.query.all()
    now = datetime.now()
    for alarm in alarms:
        # Parse time as HH:MM
        time_str = alarm.time
        hour, minute = map(int, time_str.split(':'))
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if alarm.weekdays:
            # Schedule on specific weekdays
            days = [int(d) for d in alarm.weekdays.split(',')]
            scheduler.add_job(
                id=str(alarm.id),
                func=trigger_alarm,
                args=[alarm.id],
                trigger='cron',
                hour=dt.hour,
                minute=dt.minute,
                second=dt.second,
                day_of_week=','.join(str(d) for d in days)
            )
        elif alarm.repeat_daily:
            # Schedule daily at the specified time
            scheduler.add_job(
                id=str(alarm.id),
                func=trigger_alarm,
                args=[alarm.id],
                trigger='cron',
                hour=dt.hour,
                minute=dt.minute,
                second=dt.second
            )
        else:
            # Schedule one-time if in the future
            if dt > now:
                scheduler.add_job(
                    id=str(alarm.id),
                    func=trigger_alarm,
                    args=[alarm.id],
                    trigger='date',
                    run_date=dt
                )
