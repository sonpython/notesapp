"""Backup router -- manual trigger, list, and settings endpoints.

All endpoints require authentication. Backup trigger is rate-limited to
1/hour per user to prevent abuse.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.telegram import TelegramSettings
from app.models.telegram_backup import TelegramBackup
from app.rate_limiter import limiter
from app.schemas.telegram import (
    EncryptedBackupRequest,
    EncryptedRestoreResponse,
    RestoreEntityCounts,
    RestoreResponse,
    TelegramBackupItem,
    TelegramBackupListResponse,
    TelegramBackupSettingsResponse,
    TelegramBackupSettingsUpdate,
)
from app.services.backup_export_service import (
    deserialize_backup,
    export_user_data,
    serialize_backup,
)
from app.services.backup_import_service import import_user_data
from app.services.telegram_backup_manager import (
    BackupResult,
    create_backup,
    create_encrypted_backup,
)
from app.services.telegram_service import download_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export")
async def export_backup_data(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Export user data as JSON for client-side encryption.

    Returns raw backup data that can be encrypted on the client
    before being sent to /trigger/encrypted.
    """
    data = await export_user_data(db, user_id)
    return data


@router.post("/trigger/encrypted", status_code=status.HTTP_200_OK)
@limiter.limit("1/hour")
async def trigger_encrypted_backup(
    request: Request,
    body: EncryptedBackupRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger a backup with pre-encrypted data from the client.

    The client encrypts the data using passkey PRF before sending.
    Backend stores it as-is without being able to decrypt.
    Rate-limited to 1/hour.
    """
    try:
        result: BackupResult = await create_encrypted_backup(
            db, user_id, body.encrypted_data, body.iv
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.error(
            "trigger_encrypted_backup: upload failed for user=%s: %s", user_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Backup upload to Telegram failed",
        ) from exc

    return {
        "backup_id": result.backup_id,
        "file_id": result.file_id,
        "size_bytes": result.size_bytes,
        "version": result.version,
        "counts": result.counts,
        "is_encrypted": True,
    }


@router.post("/trigger", status_code=status.HTTP_200_OK)
@limiter.limit("1/hour")
async def trigger_backup(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger a backup for the authenticated user.

    Exports all user data and uploads to Telegram as a compressed document.
    Rate-limited to 1/hour.

    Returns backup metadata on success.
    """
    try:
        result: BackupResult = await create_backup(db, user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.error("trigger_backup: upload failed for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Backup upload to Telegram failed",
        ) from exc

    return {
        "backup_id": result.backup_id,
        "file_id": result.file_id,
        "size_bytes": result.size_bytes,
        "version": result.version,
        "counts": result.counts,
    }


@router.get("/list", response_model=TelegramBackupListResponse)
async def list_backups(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramBackupListResponse:
    """List all backups for the authenticated user, newest first."""
    result = await db.execute(
        select(TelegramBackup)
        .where(TelegramBackup.user_id == UUID(user_id))
        .order_by(TelegramBackup.created_at.desc())
    )
    backups = list(result.scalars().all())

    return TelegramBackupListResponse(
        items=[TelegramBackupItem.model_validate(b) for b in backups],
        total=len(backups),
    )


@router.get("/settings", response_model=TelegramBackupSettingsResponse)
async def get_backup_settings(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramBackupSettingsResponse:
    """Return current backup settings for the authenticated user."""
    tg = await _get_or_404(db, user_id)
    return TelegramBackupSettingsResponse(
        backup_enabled=tg.backup_enabled,
        backup_schedule=tg.backup_schedule,  # type: ignore[arg-type]
        backup_retention=tg.backup_retention,
        last_backup_at=tg.last_backup_at,
        next_backup_at=tg.next_backup_at,
    )


@router.put("/settings", response_model=TelegramBackupSettingsResponse)
async def update_backup_settings(
    body: TelegramBackupSettingsUpdate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramBackupSettingsResponse:
    """Update backup settings (enabled flag, schedule, retention count)."""
    tg = await _get_or_404(db, user_id)

    if body.backup_enabled is not None:
        tg.backup_enabled = body.backup_enabled
    if body.backup_schedule is not None:
        tg.backup_schedule = body.backup_schedule
    if body.backup_retention is not None:
        tg.backup_retention = body.backup_retention

    await db.commit()
    await db.refresh(tg)

    return TelegramBackupSettingsResponse(
        backup_enabled=tg.backup_enabled,
        backup_schedule=tg.backup_schedule,  # type: ignore[arg-type]
        backup_retention=tg.backup_retention,
        last_backup_at=tg.last_backup_at,
        next_backup_at=tg.next_backup_at,
    )


@router.get("/{backup_id}/download", response_model=EncryptedRestoreResponse)
async def download_backup(
    backup_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EncryptedRestoreResponse:
    """Download backup data for client-side decryption.

    Returns raw encrypted data if the backup is encrypted,
    or plaintext data if not encrypted. Client handles decryption.
    """
    try:
        backup_uuid = UUID(backup_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup ID format",
        )

    # Verify backup belongs to requesting user
    result = await db.execute(
        select(TelegramBackup).where(
            TelegramBackup.id == backup_uuid,
            TelegramBackup.user_id == UUID(user_id),
        )
    )
    backup = result.scalar_one_or_none()
    if backup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found",
        )

    # Download from Telegram
    compressed = await download_file(backup.telegram_file_id)
    if compressed is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to download backup from Telegram",
        )

    # Decompress
    import gzip
    import json

    try:
        decompressed = gzip.decompress(compressed)
        parsed = json.loads(decompressed)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("download_backup: decompress failed for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decompress backup data",
        ) from exc

    if backup.is_encrypted:
        # Return encrypted data for client-side decryption
        return EncryptedRestoreResponse(
            backup_id=backup_id,
            version_number=backup.version_number,
            is_encrypted=True,
            encrypted_data=parsed.get("encrypted_data"),
            iv=parsed.get("iv"),
        )
    else:
        # Return plaintext data
        return EncryptedRestoreResponse(
            backup_id=backup_id,
            version_number=backup.version_number,
            is_encrypted=False,
            data=parsed,
        )


@router.post("/import", response_model=RestoreResponse)
@limiter.limit("1/hour")
async def import_backup_data(
    request: Request,
    body: dict,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreResponse:
    """Import decrypted backup data from client.

    Used after client-side decryption of an encrypted backup.
    The client sends the decrypted backup data for import.
    Rate-limited to 1/hour per user.
    """
    # Validate backup format
    version = body.get("version")
    if version != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported backup version: {version}",
        )

    # Import (upsert) all entities in a single transaction
    try:
        raw_counts = await import_user_data(db, user_id, body)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error("import_backup_data: import failed for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Import failed; no changes were applied",
        ) from exc

    logger.info("import_backup_data: user=%s counts=%s", user_id, raw_counts)

    return RestoreResponse(
        backup_id="import",
        version_number=version,
        counts={entity: RestoreEntityCounts(**c) for entity, c in raw_counts.items()},
    )


@router.post("/{backup_id}/restore", response_model=RestoreResponse)
@limiter.limit("1/hour")
async def restore_backup(
    request: Request,
    backup_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreResponse:
    """Restore user data from a specific backup stored in Telegram.

    Downloads the backup file, decompresses it, then upserts all entities
    (non-destructive: data not in backup is preserved).
    Rate-limited to 1/hour per user.

    Raises:
        404: Backup not found or belongs to another user.
        400: Decompression or version mismatch error.
        502: Telegram download failed.
    """
    try:
        backup_uuid = UUID(backup_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup ID format",
        )

    # Verify backup belongs to requesting user
    result = await db.execute(
        select(TelegramBackup).where(
            TelegramBackup.id == backup_uuid,
            TelegramBackup.user_id == UUID(user_id),
        )
    )
    backup = result.scalar_one_or_none()
    if backup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found",
        )

    # Download from Telegram
    compressed = await download_file(backup.telegram_file_id)
    if compressed is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to download backup from Telegram",
        )

    # Decompress -> parse
    try:
        data = deserialize_backup(compressed)
    except ValueError as exc:
        logger.error("restore_backup: parse failed for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Import (upsert) all entities in a single transaction
    try:
        raw_counts = await import_user_data(db, user_id, data)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error("restore_backup: import failed for user=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Restore failed; no changes were applied",
        ) from exc

    logger.info(
        "restore_backup: user=%s backup_id=%s counts=%s",
        user_id, backup_id, raw_counts,
    )

    return RestoreResponse(
        backup_id=backup_id,
        version_number=backup.version_number,
        counts={
            entity: RestoreEntityCounts(**c) for entity, c in raw_counts.items()
        },
    )


@router.post("/latest/restore", response_model=RestoreResponse)
@limiter.limit("1/hour")
async def restore_latest_backup(
    request: Request,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RestoreResponse:
    """Restore user data from the most recent backup stored in Telegram.

    Convenience endpoint; resolves the latest backup then delegates to the
    same restore pipeline as restore_backup().
    Rate-limited to 1/hour per user.

    Raises:
        404: No backups found for user.
        400: Decompression or version mismatch error.
        502: Telegram download failed.
    """
    result = await db.execute(
        select(TelegramBackup)
        .where(TelegramBackup.user_id == UUID(user_id))
        .order_by(TelegramBackup.created_at.desc())
        .limit(1)
    )
    backup = result.scalar_one_or_none()
    if backup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No backups found for this user",
        )

    # Download from Telegram
    compressed = await download_file(backup.telegram_file_id)
    if compressed is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to download backup from Telegram",
        )

    # Decompress -> parse
    try:
        data = deserialize_backup(compressed)
    except ValueError as exc:
        logger.error(
            "restore_latest_backup: parse failed for user=%s: %s", user_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Import (upsert) all entities in a single transaction
    try:
        raw_counts = await import_user_data(db, user_id, data)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error(
            "restore_latest_backup: import failed for user=%s: %s", user_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Restore failed; no changes were applied",
        ) from exc

    logger.info(
        "restore_latest_backup: user=%s backup_id=%s counts=%s",
        user_id, backup.id, raw_counts,
    )

    return RestoreResponse(
        backup_id=str(backup.id),
        version_number=backup.version_number,
        counts={
            entity: RestoreEntityCounts(**c) for entity, c in raw_counts.items()
        },
    )


async def _get_or_404(db: AsyncSession, user_id: str) -> TelegramSettings:
    """Fetch TelegramSettings or raise 404 if not linked."""
    result = await db.execute(
        select(TelegramSettings).where(
            TelegramSettings.user_id == UUID(user_id)
        )
    )
    tg = result.scalar_one_or_none()
    if tg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telegram not linked. Link your account first.",
        )
    return tg
