"""TodoFolder model for organizing todos into a nested hierarchy."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TodoFolder(Base):
    """Represents a user-owned folder for organizing todo items."""

    __tablename__ = "todo_folders"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

    name: Mapped[str] = mapped_column(sa.String, nullable=False)

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("todo_folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    sort_order: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
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

    children: Mapped[list[TodoFolder]] = relationship(
        "TodoFolder",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    parent: Mapped[TodoFolder | None] = relationship(
        "TodoFolder",
        back_populates="children",
        remote_side=[id],
    )

    todos: Mapped[list[Todo]] = relationship(  # noqa: F821
        "Todo",
        back_populates="folder",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<TodoFolder id={self.id} name={self.name!r}>"
