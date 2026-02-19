"""Note model for user-created text notes."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Note(Base):
    """Represents a user-owned note, optionally placed inside a folder."""

    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Local auth user -- no FK constraint to users table
    user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

    title: Mapped[str] = mapped_column(sa.String, nullable=False, server_default="")

    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="")

    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    is_pinned: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )

    is_archived: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
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

    folder: Mapped[Folder | None] = relationship(  # noqa: F821
        "Folder",
        back_populates="notes",
    )

    todos: Mapped[list[Todo]] = relationship(  # noqa: F821
        "Todo",
        back_populates="note",
        passive_deletes=True,
    )

    tags: Mapped[list[Tag]] = relationship(  # noqa: F821
        "Tag",
        secondary="note_tags",
        back_populates="notes",
    )

    def __repr__(self) -> str:
        return f"<Note id={self.id} title={self.title!r}>"
