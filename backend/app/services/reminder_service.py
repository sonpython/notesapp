# Reminder checking service - called by APScheduler
import asyncio
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.database import async_session_factory
from app.models.telegram import TelegramSettings
from app.models.todo import Todo
from app.services.telegram_service import send_telegram_message


async def check_and_send_reminders():
    """Check for due reminders and send Telegram notifications."""
    async with async_session_factory() as session:
        now = datetime.now(UTC)
        # Find todos with due reminders that haven't been sent
        # Join with telegram_settings to get chat_id
        stmt = (
            select(Todo, TelegramSettings.chat_id)
            .join(TelegramSettings, Todo.user_id == TelegramSettings.user_id)
            .where(
                Todo.reminder_at <= now,
                Todo.reminder_sent == False,
                TelegramSettings.chat_id.isnot(None),
                TelegramSettings.is_enabled == True,
            )
        )
        result = await session.execute(stmt)
        rows = result.all()

        for todo, chat_id in rows:
            message = f"\u23f0 *Reminder*\n\n{todo.title}"
            if todo.description:
                message += f"\n{todo.description}"
            if todo.deadline:
                message += f"\n\n\U0001f4c5 Deadline: {todo.deadline.strftime('%Y-%m-%d %H:%M')}"

            success = await send_telegram_message(chat_id, message)
            if success:
                await session.execute(
                    update(Todo).where(Todo.id == todo.id).values(reminder_sent=True)
                )
        await session.commit()


def run_reminder_check():
    """Synchronous wrapper for APScheduler."""
    asyncio.run(check_and_send_reminders())
