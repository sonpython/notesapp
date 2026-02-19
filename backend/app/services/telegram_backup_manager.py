"""Telegram backup manager -- orchestrates create_backup and prune_old_backups.

Ties together backup_export_service (export + serialize) with upload via
telegram_service.send_document(). Stores backup metadata in the
telegram_backups table and prunes old entries per user retention setting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telegram import TelegramSettings
from app.models.telegram_backup import TelegramBackup
from app.services.backup_export_service import export_user_data, serialize_backup
from app.services.telegram_service import delete_message, send_document
import base64
import gzip
import hashlib
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# Telegram file size hard limit (50 MB)
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# PBKDF2 parameters (must match client-side)
_PBKDF2_ITERATIONS = 100000
_PBKDF2_HASH = "sha256"
_KEY_LENGTH = 32  # 256 bits for AES-256


def _derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive AES-256 key from password using PBKDF2 (matches client-side)."""
    return hashlib.pbkdf2_hmac(
        _PBKDF2_HASH, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, _KEY_LENGTH
    )


def _encrypt_with_password(data: bytes, password: str) -> tuple[str, str, str]:
    """Encrypt data with password using AES-256-GCM.

    Returns (encrypted_data_b64, iv_b64, salt_b64) matching client format.
    """
    salt = os.urandom(16)
    iv = os.urandom(12)  # GCM nonce

    key = _derive_key_from_password(password, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)

    return (
        base64.b64encode(ciphertext).decode("ascii"),
        base64.b64encode(iv).decode("ascii"),
        base64.b64encode(salt).decode("ascii"),
    )


@dataclass
class BackupResult:
    """Result returned from create_backup()."""

    backup_id: str
    file_id: str
    size_bytes: int
    counts: dict
    version: int


async def _get_telegram_settings(
    db: AsyncSession, user_id: UUID
) -> TelegramSettings | None:
    """Fetch TelegramSettings row for user, or None if not found."""
    result = await db.execute(
        select(TelegramSettings).where(TelegramSettings.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _next_version_number(db: AsyncSession, user_id: UUID) -> int:
    """Return max(version_number) + 1 for user's backups, starting at 1."""
    result = await db.execute(
        select(func.max(TelegramBackup.version_number)).where(
            TelegramBackup.user_id == user_id
        )
    )
    current_max = result.scalar_one_or_none()
    return (current_max or 0) + 1


async def create_backup(
    db: AsyncSession,
    user_id: str | UUID,
) -> BackupResult:
    """Full backup pipeline: export -> serialize -> upload -> store.

    If user has backup_password set, auto-encrypts with that password.

    Steps:
    1. Verify Telegram is linked for user
    2. Export all user data
    3. Serialize to gzip-compressed JSON (or encrypt if password set)
    4. Validate size < 50 MB
    5. Upload to Telegram as document
    6. Store TelegramBackup metadata row
    7. Update TelegramSettings.last_backup_at
    8. Prune old backups per retention setting

    Args:
        db: Async database session.
        user_id: User's UUID.

    Returns:
        BackupResult with backup_id, file_id, size_bytes, counts, version.

    Raises:
        ValueError: If Telegram not linked, or backup exceeds size limit.
        RuntimeError: If Telegram upload fails.
    """
    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id

    # 1. Verify Telegram is linked
    tg = await _get_telegram_settings(db, uid)
    if not tg or not tg.chat_id:
        raise ValueError("Telegram not linked for this user")

    # 2. Export all user data
    data = await export_user_data(db, uid)
    counts = data["counts"]

    # 3. Serialize (and optionally encrypt if password is set)
    is_encrypted = False
    encryption_method = None

    if tg.backup_password:
        # Encrypt with stored password (server-side encryption)
        json_bytes = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        encrypted_data, iv, salt = _encrypt_with_password(json_bytes, tg.backup_password)

        envelope = {
            "encrypted": True,
            "encrypted_data": encrypted_data,
            "iv": iv,
            "salt": salt,  # Client needs salt for PBKDF2
        }
        compressed = gzip.compress(
            json.dumps(envelope, ensure_ascii=False).encode("utf-8"), compresslevel=6
        )
        is_encrypted = True
        encryption_method = "password"
        filename_suffix = ".enc.gz"
        caption_suffix = "(encrypted with password)"
    else:
        # Plain backup
        compressed = serialize_backup(data)
        filename_suffix = ".gz"
        caption_suffix = ""

    # 4. Size check
    if len(compressed) > _MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Backup size {len(compressed)} bytes exceeds Telegram 50 MB limit"
        )

    # 5. Upload to Telegram
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"notesapp-backup-{ts}{filename_suffix}"
    caption = (
        f"NotesApp Backup - {ts}\n"
        f"Notes: {counts['notes']}, Todos: {counts['todos']}, "
        f"Folders: {counts['folders']}, Tags: {counts['tags']}"
    )
    if caption_suffix:
        caption = f"{caption}\n{caption_suffix}"

    upload_result = await send_document(tg.chat_id, compressed, filename, caption)
    if upload_result is None:
        raise RuntimeError("Failed to upload backup to Telegram")

    file_id, message_id = upload_result

    # 6. Determine next version and store metadata
    version = await _next_version_number(db, uid)
    backup = TelegramBackup(
        user_id=uid,
        telegram_file_id=file_id,
        telegram_message_id=message_id,
        backup_size_bytes=len(compressed),
        entity_counts=counts,
        version_number=version,
        is_encrypted=is_encrypted,
        encryption_method=encryption_method,
    )
    db.add(backup)

    # 7. Update last_backup_at on settings
    tg.last_backup_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(backup)

    logger.info(
        "create_backup: user=%s version=%d size=%d bytes encrypted=%s",
        uid, version, len(compressed), is_encrypted,
    )

    # 8. Prune old backups
    await prune_old_backups(db, uid, tg.backup_retention)

    return BackupResult(
        backup_id=str(backup.id),
        file_id=file_id,
        size_bytes=len(compressed),
        counts=counts,
        version=version,
    )


async def create_encrypted_backup(
    db: AsyncSession,
    user_id: str | UUID,
    encrypted_data: str,
    iv: str,
    encryption_method: str = "prf",
) -> BackupResult:
    """Create backup from pre-encrypted data (E2E encrypted by client).

    Steps:
    1. Verify Telegram is linked for user
    2. Wrap encrypted data with IV in JSON envelope
    3. Gzip compress
    4. Validate size < 50 MB
    5. Upload to Telegram as document
    6. Store TelegramBackup metadata row (is_encrypted=True)
    7. Update TelegramSettings.last_backup_at
    8. Prune old backups per retention setting

    Args:
        db: Async database session.
        user_id: User's UUID.
        encrypted_data: Base64-encoded encrypted JSON from client.
        iv: Base64-encoded AES-GCM IV from client.
        encryption_method: "prf" (passkey PRF) or "password" (PBKDF2).

    Returns:
        BackupResult with backup_id, file_id, size_bytes, counts, version.

    Raises:
        ValueError: If Telegram not linked, or backup exceeds size limit.
        RuntimeError: If Telegram upload fails.
    """
    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id

    # 1. Verify Telegram is linked
    tg = await _get_telegram_settings(db, uid)
    if not tg or not tg.chat_id:
        raise ValueError("Telegram not linked for this user")

    # 2. Create JSON envelope with encrypted data
    envelope = {
        "encrypted": True,
        "encrypted_data": encrypted_data,
        "iv": iv,
    }
    json_bytes = json.dumps(envelope, ensure_ascii=False).encode("utf-8")

    # 3. Gzip compress
    compressed = gzip.compress(json_bytes, compresslevel=6)

    # 4. Size check
    if len(compressed) > _MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Backup size {len(compressed)} bytes exceeds Telegram 50 MB limit"
        )

    # 5. Upload to Telegram
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"notesapp-backup-{ts}.enc.gz"
    caption = f"NotesApp Encrypted Backup - {ts}\n(E2E encrypted with passkey)"

    upload_result = await send_document(tg.chat_id, compressed, filename, caption)
    if upload_result is None:
        raise RuntimeError("Failed to upload backup to Telegram")

    file_id, message_id = upload_result

    # 6. Determine next version and store metadata
    version = await _next_version_number(db, uid)
    backup = TelegramBackup(
        user_id=uid,
        telegram_file_id=file_id,
        telegram_message_id=message_id,
        backup_size_bytes=len(compressed),
        entity_counts={"encrypted": True},  # Can't see counts for encrypted backup
        version_number=version,
        is_encrypted=True,
        encryption_method=encryption_method,
    )
    db.add(backup)

    # 7. Update last_backup_at on settings
    tg.last_backup_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(backup)

    logger.info(
        "create_encrypted_backup: user=%s version=%d size=%d bytes (encrypted)",
        uid, version, len(compressed),
    )

    # 8. Prune old backups
    await prune_old_backups(db, uid, tg.backup_retention)

    return BackupResult(
        backup_id=str(backup.id),
        file_id=file_id,
        size_bytes=len(compressed),
        counts={"encrypted": True},
        version=version,
    )


async def prune_old_backups(
    db: AsyncSession,
    user_id: UUID,
    retention_count: int,
) -> int:
    """Delete TelegramBackup rows + Telegram messages exceeding retention limit.

    Keeps the most recent `retention_count` backups; deletes the rest.

    Args:
        db: Async database session.
        user_id: User's UUID.
        retention_count: Number of backups to retain (oldest beyond this are pruned).

    Returns:
        Number of backups deleted.
    """
    # Fetch all backups ordered oldest first
    result = await db.execute(
        select(TelegramBackup)
        .where(TelegramBackup.user_id == user_id)
        .order_by(TelegramBackup.created_at.asc())
    )
    all_backups = list(result.scalars().all())

    to_delete = all_backups[: max(0, len(all_backups) - retention_count)]
    if not to_delete:
        return 0

    # Fetch chat_id for Telegram message deletion
    tg = await _get_telegram_settings(db, user_id)
    chat_id = tg.chat_id if tg else None

    deleted_count = 0
    for backup in to_delete:
        # Delete Telegram message (best-effort; don't fail if already gone)
        if chat_id and backup.telegram_message_id is not None:
            success = await delete_message(chat_id, backup.telegram_message_id)
            if not success:
                logger.warning(
                    "prune_old_backups: could not delete Telegram message %s for backup %s",
                    backup.telegram_message_id,
                    backup.id,
                )

        await db.delete(backup)
        deleted_count += 1

    if deleted_count:
        await db.commit()
        logger.info(
            "prune_old_backups: user=%s pruned=%d (retention=%d)",
            user_id, deleted_count, retention_count,
        )

    return deleted_count
