"""Todo model for task items, optionally linked to a note."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Todo(Base):
    """Represents a user-owned to-do item with optional hierarchy and note link."""

    __tablename__ = "todos"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Supabase-managed auth.users -- no FK constraint
    user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

    title: Mapped[str] = mapped_column(sa.String, nullable=False)

    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    is_completed: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false"),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True,
    )

    deadline: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True,
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("todos.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    note_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 0=none, 1=low, 2=medium, 3=high
    priority: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0"),
    )

    sort_order: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0"),
    )

    reminder_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True,
    )

    reminder_sent: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false"),
    )

    # -- Recurrence fields ------------------------------------------------------

    # Recurrence type: null=none, 'daily', 'weekly', 'monthly', 'custom'
    recurrence_type: Mapped[str | None] = mapped_column(
        sa.String(20), nullable=True,
    )

    # Interval multiplier (e.g., every 2 weeks = type='weekly', interval=2)
    recurrence_interval: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True, server_default=sa.text("1"),
    )

    # For weekly: comma-separated weekday numbers (0=Mon, 6=Sun)
    # For monthly: day of month (1-31)
    # null for daily
    recurrence_days: Mapped[str | None] = mapped_column(
        sa.String(20), nullable=True,
    )

    # Stop recurring after this date; null = forever
    recurrence_end_date: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True,
    )

    # Links back to original recurring todo (for tracking lineage)
    recurrence_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("todos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    # -- Relationships ----------------------------------------------------------

    parent: Mapped[Todo | None] = relationship(
        "Todo",
        foreign_keys=[parent_id],
        back_populates="children",
        remote_side=[id],
    )

    children: Mapped[list[Todo]] = relationship(
        "Todo",
        foreign_keys=[parent_id],
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    note: Mapped["Note | None"] = relationship(  # noqa: F821
        "Note",
        back_populates="todos",
    )

    recurrence_parent: Mapped[Todo | None] = relationship(
        "Todo",
        foreign_keys=[recurrence_parent_id],
        remote_side=[id],
    )

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag",
        secondary="todo_tags",
        back_populates="todos",
    )

    def __repr__(self) -> str:
        return f"<Todo id={self.id} title={self.title!r}>"
