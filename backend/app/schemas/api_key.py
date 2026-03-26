from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str
    expires_at: datetime | None = None  # null = never expires


class ApiKeyCreateResponse(BaseModel):
    """Returned only once at creation — includes the full plaintext key."""

    id: UUID
    name: str
    key: str  # full plaintext key (shown only once)
    key_prefix: str
    expires_at: datetime | None
    created_at: datetime


class ApiKeyResponse(BaseModel):
    """List/display response — never includes the full key."""

    id: UUID
    name: str
    key_prefix: str
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
