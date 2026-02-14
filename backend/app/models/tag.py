"""Tag model and junction tables for notes and todos."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tag(Base):
    """User-scoped tag for organizing notes and todos."""

    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Supabase-managed auth.users -- no FK constraint
    user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)

    color: Mapped[str] = mapped_column(
        sa.String(7),
        nullable=False,
        server_default="#6b7280",
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # Unique constraint: one user cannot have duplicate tag names
    __table_args__ = (
        sa.UniqueConstraint("user_id", "name", name="uq_tags_user_id_name"),
    )

    # -- Relationships ----------------------------------------------------------

    notes: Mapped[list["Note"]] = relationship(  # noqa: F821
        "Note",
        secondary="note_tags",
        back_populates="tags",
    )

    todos: Mapped[list["Todo"]] = relationship(  # noqa: F821
        "Todo",
        secondary="todo_tags",
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r} color={self.color}>"


class NoteTag(Base):
    """Junction table linking notes to tags (many-to-many)."""

    __tablename__ = "note_tags"

    note_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tag_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # For "find all notes with tag X" queries
    )

    def __repr__(self) -> str:
        return f"<NoteTag note_id={self.note_id} tag_id={self.tag_id}>"


class TodoTag(Base):
    """Junction table linking todos to tags (many-to-many)."""

    __tablename__ = "todo_tags"

    todo_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("todos.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tag_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # For "find all todos with tag X" queries
    )

    def __repr__(self) -> str:
        return f"<TodoTag todo_id={self.todo_id} tag_id={self.tag_id}>"
