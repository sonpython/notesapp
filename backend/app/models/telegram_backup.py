"""TelegramBackup model -- tracks backup metadata stored in Telegram."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelegramBackup(Base):
    """One row per backup file uploaded to Telegram.

    Stores enough metadata so restore logic can locate and download the file
    via the Telegram Bot API without re-uploading.
    """

    __tablename__ = "telegram_backups"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Supabase-managed auth.users -- no FK constraint (same pattern as other models)
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, nullable=False, index=True,
    )

    # Persistent Telegram file identifier -- survives message deletion
    telegram_file_id: Mapped[str] = mapped_column(sa.String, nullable=False)

    # Message ID in the Telegram chat (needed for deleteMessage cleanup)
    telegram_message_id: Mapped[int | None] = mapped_column(
        sa.Integer, nullable=True,
    )

    # Size of the backup in bytes
    backup_size_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)

    # JSONB dict with entity counts, e.g. {"notes": 42, "todos": 5, "folders": 3}
    entity_counts: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"),
    )

    # Monotonically increasing version (incremented per backup run)
    version_number: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("1"),
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<TelegramBackup id={self.id} user_id={self.user_id} "
            f"version={self.version_number}>"
        )
