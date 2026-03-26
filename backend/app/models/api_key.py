"""API key model for MCP and external integrations."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ApiKey(Base):
    """User-owned API key for MCP server authentication."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False, index=True)

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    # SHA-256 hash of the key (never store plaintext)
    key_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)

    # First 8 chars for display identification (e.g. "na_k1x2y3z4...")
    key_prefix: Mapped[str] = mapped_column(sa.String(16), nullable=False)

    expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,  # null = never expires
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    def __repr__(self) -> str:
        return f"<ApiKey id={self.id} name={self.name!r} prefix={self.key_prefix}>"
