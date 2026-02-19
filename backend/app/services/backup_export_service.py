"""Export and serialize user data for backup.

Fetches notes, todos, folders, tags for a given user, then serializes and
gzip-compresses the result into bytes ready for upload.
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.folder import Folder
from app.models.note import Note
from app.models.tag import Tag
from app.models.todo import Todo

logger = logging.getLogger(__name__)

BACKUP_VERSION = 1
APP_VERSION = "0.1.0"


def _dt_to_str(dt: datetime | None) -> str | None:
    """Convert datetime to ISO-8601 UTC string, or None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _note_to_dict(note: Note) -> dict:
    return {
        "id": str(note.id),
        "title": note.title,
        "content": note.content,
        "folder_id": str(note.folder_id) if note.folder_id else None,
        "is_pinned": note.is_pinned,
        "is_archived": note.is_archived,
        "created_at": _dt_to_str(note.created_at),
        "updated_at": _dt_to_str(note.updated_at),
        "tag_ids": [str(t.id) for t in note.tags],
    }


def _todo_to_dict(todo: Todo) -> dict:
    return {
        "id": str(todo.id),
        "title": todo.title,
        "description": todo.description,
        "is_completed": todo.is_completed,
        "completed_at": _dt_to_str(todo.completed_at),
        "deadline": _dt_to_str(todo.deadline),
        "parent_id": str(todo.parent_id) if todo.parent_id else None,
        "note_id": str(todo.note_id) if todo.note_id else None,
        "priority": todo.priority,
        "sort_order": todo.sort_order,
        "reminder_at": _dt_to_str(todo.reminder_at),
        "recurrence_type": todo.recurrence_type,
        "recurrence_interval": todo.recurrence_interval,
        "recurrence_days": todo.recurrence_days,
        "recurrence_end_date": _dt_to_str(todo.recurrence_end_date),
        "created_at": _dt_to_str(todo.created_at),
        "updated_at": _dt_to_str(todo.updated_at),
        "tag_ids": [str(t.id) for t in todo.tags],
    }


def _folder_to_dict(folder: Folder) -> dict:
    return {
        "id": str(folder.id),
        "name": folder.name,
        "parent_id": str(folder.parent_id) if folder.parent_id else None,
        "icon": folder.icon,
        "created_at": _dt_to_str(folder.created_at),
        "updated_at": _dt_to_str(folder.updated_at),
    }


def _tag_to_dict(tag: Tag) -> dict:
    return {
        "id": str(tag.id),
        "name": tag.name,
        "color": tag.color,
        "created_at": _dt_to_str(tag.created_at),
    }


async def export_user_data(
    db: AsyncSession,
    user_id: str | UUID,
) -> dict:
    """Fetch all user entities and return as a structured dict.

    Args:
        db: Async database session.
        user_id: User's UUID (str or UUID).

    Returns:
        Dict conforming to the backup JSON schema (version, created_at, data, counts).
    """
    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id

    # --- Notes with tags ---
    notes_result = await db.execute(
        select(Note)
        .where(Note.user_id == uid)
        .options(selectinload(Note.tags))
        .order_by(Note.created_at)
    )
    notes = list(notes_result.scalars().all())

    # --- Todos with tags ---
    todos_result = await db.execute(
        select(Todo)
        .where(Todo.user_id == uid)
        .options(selectinload(Todo.tags))
        .order_by(Todo.created_at)
    )
    todos = list(todos_result.scalars().all())

    # --- Folders ---
    folders_result = await db.execute(
        select(Folder).where(Folder.user_id == uid).order_by(Folder.created_at)
    )
    folders = list(folders_result.scalars().all())

    # --- Tags ---
    tags_result = await db.execute(select(Tag).where(Tag.user_id == uid).order_by(Tag.created_at))
    tags = list(tags_result.scalars().all())

    counts = {
        "notes": len(notes),
        "todos": len(todos),
        "folders": len(folders),
        "tags": len(tags),
    }

    logger.info("export_user_data: user=%s counts=%s", uid, counts)

    return {
        "version": BACKUP_VERSION,
        "app_version": APP_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "user_id": str(uid),
        "data": {
            "notes": [_note_to_dict(n) for n in notes],
            "todos": [_todo_to_dict(t) for t in todos],
            "folders": [_folder_to_dict(f) for f in folders],
            "tags": [_tag_to_dict(t) for t in tags],
        },
        "counts": counts,
    }


def serialize_backup(data: dict) -> bytes:
    """JSON-serialize the backup dict and gzip-compress it.

    Args:
        data: Structured backup dict from export_user_data().

    Returns:
        Gzip-compressed JSON bytes.
    """
    json_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(json_bytes, compresslevel=6)
    logger.debug(
        "serialize_backup: json=%d bytes -> compressed=%d bytes (%.1fx)",
        len(json_bytes),
        len(compressed),
        len(json_bytes) / max(len(compressed), 1),
    )
    return compressed


def deserialize_backup(data: bytes) -> dict:
    """Gzip-decompress and JSON-parse a serialized backup payload.

    Inverse of serialize_backup(). Validates that the parsed dict has a
    supported version field.

    Args:
        data: Gzip-compressed JSON bytes (as returned by serialize_backup).

    Returns:
        Parsed backup dict.

    Raises:
        ValueError: If decompression, JSON parsing, or version check fails.
    """
    try:
        json_bytes = gzip.decompress(data)
    except OSError as exc:
        raise ValueError(f"Failed to decompress backup: {exc}") from exc

    try:
        parsed = json.loads(json_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse backup JSON: {exc}") from exc

    version = parsed.get("version")
    if version != BACKUP_VERSION:
        raise ValueError(f"Unsupported backup version: {version!r} (expected {BACKUP_VERSION})")

    logger.debug("deserialize_backup: version=%s ok", version)
    return parsed
