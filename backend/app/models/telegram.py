"""TelegramSettings model for per-user Telegram bot integration."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelegramSettings(Base):
    """Stores Telegram bot integration settings for a single user."""

    __tablename__ = "telegram_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Supabase-managed auth.users -- no FK constraint. One row per user.
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, nullable=False, unique=True, index=True,
    )

    chat_id: Mapped[str | None] = mapped_column(sa.String, nullable=True)

    is_enabled: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("true"),
    )

    link_code: Mapped[str | None] = mapped_column(sa.String, nullable=True)

    bot_linked_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    def __repr__(self) -> str:
        return f"<TelegramSettings id={self.id} user_id={self.user_id}>"
