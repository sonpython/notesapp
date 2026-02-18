"""PasskeyCredential model for WebAuthn credentials."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class PasskeyCredential(Base):
    """WebAuthn credential (passkey) associated with a user.

    A user can have multiple passkeys (e.g., phone + laptop).
    """

    __tablename__ = "passkey_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # WebAuthn credential ID (binary, unique across all credentials)
    credential_id: Mapped[bytes] = mapped_column(
        sa.LargeBinary,
        nullable=False,
        unique=True,
    )

    # WebAuthn public key (binary, COSE format)
    public_key: Mapped[bytes] = mapped_column(
        sa.LargeBinary,
        nullable=False,
    )

    # Authenticator sign counter for cloning detection
    sign_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )

    # Transports (JSON array as string, e.g., '["internal","hybrid"]')
    transports: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )

    # Whether credential is backed up to cloud
    backed_up: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )

    # Device type: 'single_device' or 'multi_device'
    device_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="single_device",
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # -- Relationships ----------------------------------------------------------

    user: Mapped["User"] = relationship(
        "User",
        back_populates="passkey_credentials",
    )

    def __repr__(self) -> str:
        return f"<PasskeyCredential id={self.id} user_id={self.user_id}>"
