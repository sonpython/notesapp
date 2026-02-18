# APScheduler setup for periodic background tasks
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.services.reminder_service import check_and_send_reminders
from app.tasks.telegram_backup_scheduler import check_and_run_scheduled_backups

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def cleanup_webauthn_challenges():
    """Delete expired WebAuthn challenges."""
    from app.database import async_session_factory
    from app.services.webauthn_service import cleanup_expired_challenges

    async with async_session_factory() as db:
        deleted = await cleanup_expired_challenges(db)
        if deleted > 0:
            logger.info("Cleaned up %d expired WebAuthn challenges", deleted)


def start_scheduler():
    scheduler.add_job(
        check_and_send_reminders,
        'interval',
        seconds=60,
        id='reminder_check',
        replace_existing=True,
    )
    scheduler.add_job(
        cleanup_webauthn_challenges,
        'interval',
        minutes=10,
        id='webauthn_challenge_cleanup',
        replace_existing=True,
    )
    scheduler.add_job(
        check_and_run_scheduled_backups,
        'interval',
        minutes=15,
        id='telegram_backup_check',
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
