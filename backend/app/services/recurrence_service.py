"""Recurrence logic for generating next todo occurrences."""

from __future__ import annotations

from datetime import UTC, datetime

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, rrule
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo

FREQ_MAP = {
    "daily": DAILY,
    "weekly": WEEKLY,
    "monthly": MONTHLY,
}


def compute_next_date(
    base_date: datetime,
    recurrence_type: str,
    interval: int = 1,
    recurrence_days: str | None = None,
) -> datetime | None:
    """Compute next occurrence date from base_date using dateutil.rrule.

    Args:
        base_date: Starting date for recurrence calculation
        recurrence_type: One of 'daily', 'weekly', 'monthly'
        interval: Recurrence interval (e.g., every 2 weeks)
        recurrence_days: For weekly: comma-separated weekday numbers (0=Mon, 6=Sun)

    Returns:
        Next occurrence datetime or None if unable to compute
    """
    freq = FREQ_MAP.get(recurrence_type)
    if freq is None:
        return None

    byweekday = None
    if recurrence_type == "weekly" and recurrence_days:
        try:
            byweekday = [int(d) for d in recurrence_days.split(",")]
        except ValueError:
            return None

    try:
        rule = rrule(
            freq=freq,
            interval=interval,
            dtstart=base_date,
            byweekday=byweekday,
            count=2,  # current + next
        )
        dates = list(rule)
        return dates[1] if len(dates) > 1 else None
    except Exception:
        return None


async def create_next_occurrence(
    todo: Todo,
    session: AsyncSession,
) -> Todo | None:
    """Create next recurring todo after completion.

    Args:
        todo: Completed todo with recurrence settings
        session: Database session for creating new todo

    Returns:
        Newly created todo or None if recurrence stopped or invalid
    """
    if not todo.recurrence_type:
        return None

    # Use deadline as base, fallback to completed_at or now
    base = todo.deadline or todo.completed_at or datetime.now(UTC)

    next_date = compute_next_date(
        base,
        todo.recurrence_type,
        todo.recurrence_interval or 1,
        todo.recurrence_days,
    )

    if next_date is None:
        return None

    # Stop if next date exceeds end date
    if todo.recurrence_end_date and next_date > todo.recurrence_end_date:
        return None

    # Preserve reminder offset from deadline
    reminder_offset = None
    if todo.reminder_at and todo.deadline:
        reminder_offset = todo.deadline - todo.reminder_at

    new_todo = Todo(
        user_id=todo.user_id,
        title=todo.title,
        description=todo.description,
        priority=todo.priority,
        sort_order=todo.sort_order,
        parent_id=todo.parent_id,
        note_id=todo.note_id,
        deadline=next_date,
        reminder_at=(next_date - reminder_offset) if reminder_offset else None,
        recurrence_type=todo.recurrence_type,
        recurrence_interval=todo.recurrence_interval,
        recurrence_days=todo.recurrence_days,
        recurrence_end_date=todo.recurrence_end_date,
        recurrence_parent_id=todo.recurrence_parent_id or todo.id,
    )
    session.add(new_todo)
    return new_todo
