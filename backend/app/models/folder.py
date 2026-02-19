"""Folder model for organizing notes into a nested hierarchy."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Folder(Base):
    """Represents a user-owned folder that can contain notes and sub-folders."""

    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Local auth user -- no FK constraint to users table
    user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

    name: Mapped[str] = mapped_column(sa.String, nullable=False)

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    icon: Mapped[str | None] = mapped_column(sa.String, nullable=True)

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

    children: Mapped[list[Folder]] = relationship(
        "Folder",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    parent: Mapped[Folder | None] = relationship(
        "Folder",
        back_populates="children",
        remote_side=[id],
    )

    notes: Mapped[list[Note]] = relationship(  # noqa: F821
        "Note",
        back_populates="folder",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Folder id={self.id} name={self.name!r}>"
