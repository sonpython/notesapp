"""SharedNote model for publicly shared notes with optional protection."""

from __future__ import annotations

import secrets
import string
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_pub_id() -> str:
    """Generate a 6-character alphanumeric ID (case-sensitive)."""
    chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
    return "".join(secrets.choice(chars) for _ in range(6))


class SharedNote(Base):
    """Represents a publicly shared note with optional expiry, view limit, and password."""

    __tablename__ = "shared_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    note_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 6-char alphanumeric public ID for URL
    pub_id: Mapped[str] = mapped_column(
        sa.String(6),
        nullable=False,
        unique=True,
        index=True,
        default=generate_pub_id,
    )

    # Optional password protection (bcrypt hash)
    password_hash: Mapped[str | None] = mapped_column(sa.String, nullable=True)

    # Optional expiration
    expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Optional view limit
    max_views: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    view_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # Relationship to Note
    note: Mapped[Note] = relationship("Note", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return f"<SharedNote pub_id={self.pub_id} note_id={self.note_id}>"
