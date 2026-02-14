"""Query-building helpers for the todos router."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.sql import Select

from app.models.todo import Todo


def build_todos_list_query(
    *,
    user_id: str,
    is_completed: bool | None = None,
    priority: int | None = None,
    has_deadline: bool | None = None,
    note_id: UUID | None = None,
) -> Select:
    """Build a SELECT for listing top-level todos with optional filters.

    Only returns todos where ``parent_id IS NULL`` (top-level).
    Orders by sort_order ASC, then created_at ASC.
    """
    stmt = select(Todo).where(
        Todo.user_id == user_id,
        Todo.parent_id.is_(None),
    )

    if is_completed is not None:
        stmt = stmt.where(Todo.is_completed == is_completed)

    if priority is not None:
        stmt = stmt.where(Todo.priority == priority)

    if has_deadline is not None:
        if has_deadline:
            stmt = stmt.where(Todo.deadline.isnot(None))
        else:
            stmt = stmt.where(Todo.deadline.is_(None))

    if note_id is not None:
        stmt = stmt.where(Todo.note_id == note_id)

    stmt = stmt.order_by(Todo.sort_order.asc(), Todo.created_at.asc())

    return stmt


def toggle_todo_completion(todo: Todo) -> None:
    """Flip is_completed and set/clear completed_at."""
    todo.is_completed = not todo.is_completed
    todo.completed_at = datetime.now(timezone.utc) if todo.is_completed else None
