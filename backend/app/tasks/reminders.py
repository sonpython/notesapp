# APScheduler setup for periodic reminder checks
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.reminder_service import check_and_send_reminders

scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.add_job(
        check_and_send_reminders,
        'interval',
        seconds=60,
        id='reminder_check',
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
