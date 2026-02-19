"""Scheduled backup dispatcher -- checks for due backups every 15 minutes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database import async_session_factory
from app.models.telegram import TelegramSettings

logger = logging.getLogger(__name__)

# Guard against thundering herd: max backups processed per scheduler run
MAX_BACKUPS_PER_RUN = 10


def compute_next_backup_at(schedule: str, from_time: datetime) -> datetime:
    """Compute next backup time based on schedule.

    Daily: next day at 03:00 UTC (if already past 03:00 today, use tomorrow)
    Weekly: next Sunday at 03:00 UTC (always at least 1 day ahead)

    Args:
        schedule: 'daily' or 'weekly'.
        from_time: Reference time (timezone-aware UTC datetime).

    Returns:
        Next scheduled backup datetime in UTC.
    """
    if schedule == "daily":
        next_run = from_time.replace(hour=3, minute=0, second=0, microsecond=0)
        if next_run <= from_time:
            next_run += timedelta(days=1)
        return next_run

    if schedule == "weekly":
        # Days until Sunday: weekday() returns 0=Mon .. 6=Sun
        days_until_sunday = (6 - from_time.weekday()) % 7 or 7
        next_run = from_time.replace(hour=3, minute=0, second=0, microsecond=0) + timedelta(
            days=days_until_sunday
        )
        if next_run <= from_time:
            next_run += timedelta(days=7)
        return next_run

    # Fallback: treat unknown schedule as daily
    return from_time.replace(hour=3, minute=0, second=0, microsecond=0) + timedelta(days=1)


async def check_and_run_scheduled_backups() -> None:
    """Query users with due backups and run them sequentially.

    Runs every 15 minutes via APScheduler. Limits to MAX_BACKUPS_PER_RUN
    per cycle to avoid Telegram rate limiting.

    Failures per user are logged and skipped; other users continue normally.
    """
    # Import inside function to avoid circular imports at module load time
    from app.services.telegram_backup_manager import create_backup

    async with async_session_factory() as session:
        now = datetime.now(UTC)

        stmt = (
            select(TelegramSettings)
            .where(
                TelegramSettings.backup_enabled == True,  # noqa: E712
                TelegramSettings.next_backup_at <= now,
                TelegramSettings.chat_id.isnot(None),
            )
            .limit(MAX_BACKUPS_PER_RUN)
        )

        result = await session.execute(stmt)
        due_settings = list(result.scalars().all())

    if not due_settings:
        return

    logger.info("Scheduled backup: %d user(s) due", len(due_settings))

    for tg in due_settings:
        user_id = tg.user_id
        schedule = tg.backup_schedule or "daily"

        try:
            async with async_session_factory() as backup_session:
                # Run full backup pipeline (export -> upload -> store)
                await create_backup(backup_session, user_id)

                # Advance next_backup_at after successful backup
                now_after = datetime.now(UTC)
                tg_row = await backup_session.get(TelegramSettings, tg.id)
                if tg_row is not None:
                    tg_row.next_backup_at = compute_next_backup_at(schedule, now_after)
                    await backup_session.commit()

            logger.info("Scheduled backup completed for user=%s", user_id)

        except Exception:
            logger.exception("Scheduled backup failed for user=%s; skipping", user_id)
