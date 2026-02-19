import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TelegramStatusResponse(BaseModel):
    is_linked: bool
    is_enabled: bool
    chat_id: str | None = None
    bot_linked_at: datetime | None = None


class TelegramLinkResponse(BaseModel):
    link_code: str
    bot_username: str


class TelegramWebhookPayload(BaseModel):
    """Simplified Telegram webhook update"""
    update_id: int
    message: dict | None = None
    callback_query: dict | None = None  # For inline keyboard button clicks


# --- Backup settings schemas ---

BackupSchedule = Literal["daily", "weekly"]


class TelegramBackupSettingsUpdate(BaseModel):
    """Request body for updating backup settings."""
    backup_enabled: bool | None = None
    backup_schedule: BackupSchedule | None = None
    backup_retention: int | None = Field(default=None, ge=1, le=20)
    backup_password: str | None = Field(default=None, min_length=4, max_length=128)
    clear_backup_password: bool = False  # Set True to remove stored password


class TelegramBackupSettingsResponse(BaseModel):
    """Current backup settings for a user."""
    backup_enabled: bool
    backup_schedule: BackupSchedule | None
    backup_retention: int
    has_backup_password: bool = False  # True if password is set for auto-encrypted backups
    last_backup_at: datetime | None = None
    next_backup_at: datetime | None = None


class TelegramBackupItem(BaseModel):
    """Single backup entry returned in list responses."""
    id: uuid.UUID
    telegram_file_id: str
    telegram_message_id: int | None
    backup_size_bytes: int
    entity_counts: dict
    version_number: int
    is_encrypted: bool = False
    encryption_method: str | None = None  # "prf", "password", or null
    created_at: datetime

    model_config = {"from_attributes": True}


class TelegramBackupListResponse(BaseModel):
    """Paginated list of backups for a user."""
    items: list[TelegramBackupItem]
    total: int


class RestoreEntityCounts(BaseModel):
    """Created/updated/skipped counts for one entity type during restore."""
    created: int = 0
    updated: int = 0
    skipped: int = 0


class RestoreResponse(BaseModel):
    """Result of a restore operation."""
    backup_id: str
    version_number: int
    counts: dict[str, RestoreEntityCounts]


class EncryptedBackupRequest(BaseModel):
    """Request body for encrypted backup trigger."""
    encrypted_data: str  # Base64-encoded encrypted JSON
    iv: str  # Base64-encoded AES-GCM IV
    encryption_method: str = "prf"  # "prf" (passkey PRF) or "password"


class EncryptedRestoreResponse(BaseModel):
    """Response for encrypted backup restore (returns raw encrypted data)."""
    backup_id: str
    version_number: int
    is_encrypted: bool
    encryption_method: str | None = None  # "prf", "password", or null (unencrypted)
    encrypted_data: str | None = None  # Base64-encoded encrypted JSON (if encrypted)
    iv: str | None = None  # Base64-encoded IV (if encrypted)
    data: dict | None = None  # Plaintext data (if not encrypted)
