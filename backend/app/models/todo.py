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
        back_populates="children",
        remote_side=[id],
    )

    children: Mapped[list[Todo]] = relationship(
        "Todo",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    note: Mapped["Note | None"] = relationship(  # noqa: F821
        "Note",
        back_populates="todos",
    )

    def __repr__(self) -> str:
        return f"<Todo id={self.id} title={self.title!r}>"
