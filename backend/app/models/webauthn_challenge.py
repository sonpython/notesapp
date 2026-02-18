"""WebAuthnChallenge model for ephemeral challenge storage."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WebAuthnChallenge(Base):
    """Ephemeral challenge storage for WebAuthn ceremonies.

    Challenges must be stored server-side to prevent replay attacks.
    TTL: 5 minutes. Cleanup via background scheduler.
    """

    __tablename__ = "webauthn_challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Base64-encoded challenge string
    challenge: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )

    # User ID for registration (NULL for login with discoverable credentials)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        nullable=True,
    )

    # Display name (stored during registration flow)
    display_name: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )

    # Challenge type: 'register' or 'login'
    type: Mapped[str] = mapped_column(
        sa.String(10),
        nullable=False,
    )

    # When the challenge expires (typically NOW + 5 minutes)
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    def __repr__(self) -> str:
        return f"<WebAuthnChallenge id={self.id} type={self.type}>"
