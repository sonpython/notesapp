"""SharedTodoFolder model -- public link to a todo folder with optional editable mode."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.shared_note import generate_pub_id


class SharedTodoFolder(Base):
    """Represents a publicly shared todo folder.

    Mirrors `SharedNote` pattern (password / expiry / max_views) but adds
    `is_editable` to allow recipients to add/edit/delete/toggle/reorder todos
    within the shared folder. Sub-folders are intentionally hidden from the
    public view -- only direct todos in the shared folder are exposed.
    """

    __tablename__ = "shared_todo_folders"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    todo_folder_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("todo_folders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 6-char alphanumeric public ID for URL (separate namespace from shared_notes)
    pub_id: Mapped[str] = mapped_column(
        sa.String(6),
        nullable=False,
        unique=True,
        index=True,
        default=generate_pub_id,
    )

    # Optional bcrypt password protection
    password_hash: Mapped[str | None] = mapped_column(sa.String, nullable=True)

    # Optional expiration timestamp
    expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Optional view limit; view_count counts /access invocations
    max_views: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    view_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )

    # When true, recipients can mutate todos in this folder
    is_editable: Mapped[bool] = mapped_column(
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

    todo_folder: Mapped[TodoFolder] = relationship(  # noqa: F821
        "TodoFolder", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<SharedTodoFolder pub_id={self.pub_id} folder_id={self.todo_folder_id}>"
