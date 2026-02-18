"""Import (restore) user data from a deserialized backup dict.

Pipeline:
  gzip bytes -> JSON parse (in backup_export_service) -> import_user_data (this module)

Entity ordering (respects FK dependencies):
  1. Tags   (no deps)
  2. Folders (self-ref parent_id -- sorted by depth)
  3. Notes   (folder_id FK)
  4. Todos   (parent_id self-ref, note_id FK)
  5. Junction tables: note_tags, todo_tags
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.folder import Folder
from app.models.note import Note
from app.models.tag import Tag, NoteTag, TodoTag
from app.models.todo import Todo

logger = logging.getLogger(__name__)

# Fields never copied during upsert (managed separately or immutable)
_SKIP_FIELDS = frozenset({"id", "user_id", "tag_ids"})


# ---------------------------------------------------------------------------
# Datetime parsing
# ---------------------------------------------------------------------------


def _parse_dt(value: str | None) -> datetime | None:
    """Parse ISO-8601 string to datetime, or return None."""
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Folder depth sorting (handles self-referential parent_id)
# ---------------------------------------------------------------------------


def _sort_folders_by_depth(folders: list[dict]) -> list[dict]:
    """Topological sort: parents before children.

    Detects cycles by limiting depth to len(folders). Cycles are broken by
    appending cyclic nodes at the end.
    """
    id_to_folder = {f["id"]: f for f in folders}
    ordered: list[dict] = []
    visited: set[str] = set()

    def visit(fid: str, depth: int = 0) -> None:
        if fid in visited or depth > len(folders):
            return
        folder = id_to_folder.get(fid)
        if folder is None:
            return
        parent_id = folder.get("parent_id")
        if parent_id and parent_id in id_to_folder and parent_id not in visited:
            visit(parent_id, depth + 1)
        if fid not in visited:
            visited.add(fid)
            ordered.append(folder)

    for f in folders:
        visit(f["id"])

    # Append any not yet visited (e.g., circular references)
    for f in folders:
        if f["id"] not in visited:
            ordered.append(f)

    return ordered


# ---------------------------------------------------------------------------
# Generic upsert helper
# ---------------------------------------------------------------------------


async def _upsert_entity(
    session: AsyncSession,
    model_class: type,
    user_id: UUID,
    entity_data: dict,
    field_parsers: dict[str, Any] | None = None,
) -> str:
    """Upsert a single entity by ID.

    Args:
        session: Async DB session.
        model_class: SQLAlchemy model class.
        user_id: Owning user's UUID.
        entity_data: Dict of fields from backup (including 'id').
        field_parsers: Optional mapping of field_name -> callable for type conversion.

    Returns:
        'created', 'updated', or 'skipped'.
    """
    entity_id = UUID(entity_data["id"])
    existing = await session.get(model_class, entity_id)

    if existing is not None:
        if str(existing.user_id) != str(user_id):
            # ID belongs to a different user -- skip to prevent data leak
            logger.warning(
                "_upsert_entity: ID %s belongs to different user, skipping", entity_id
            )
            return "skipped"
        # Update existing fields
        for key, value in entity_data.items():
            if key in _SKIP_FIELDS:
                continue
            if field_parsers and key in field_parsers:
                value = field_parsers[key](value)
            setattr(existing, key, value)
        return "updated"
    else:
        # Insert new entity
        init_data: dict = {"id": entity_id, "user_id": user_id}
        for key, value in entity_data.items():
            if key in _SKIP_FIELDS:
                continue
            if field_parsers and key in field_parsers:
                value = field_parsers[key](value)
            init_data[key] = value
        obj = model_class(**init_data)
        session.add(obj)
        return "created"


# ---------------------------------------------------------------------------
# Junction table helpers
# ---------------------------------------------------------------------------


async def _restore_note_tags(
    session: AsyncSession,
    note_id: UUID,
    tag_ids: list[str],
    valid_tag_ids: set[str],
) -> None:
    """Replace note's tag associations with those from backup.

    Only links tags that exist in valid_tag_ids to avoid FK violations.
    """
    # Remove existing associations for this note
    await session.execute(delete(NoteTag).where(NoteTag.note_id == note_id))
    for tid_str in tag_ids:
        if tid_str not in valid_tag_ids:
            logger.debug("_restore_note_tags: tag %s not found, skipping", tid_str)
            continue
        session.add(NoteTag(note_id=note_id, tag_id=UUID(tid_str)))


async def _restore_todo_tags(
    session: AsyncSession,
    todo_id: UUID,
    tag_ids: list[str],
    valid_tag_ids: set[str],
) -> None:
    """Replace todo's tag associations with those from backup."""
    await session.execute(delete(TodoTag).where(TodoTag.todo_id == todo_id))
    for tid_str in tag_ids:
        if tid_str not in valid_tag_ids:
            logger.debug("_restore_todo_tags: tag %s not found, skipping", tid_str)
            continue
        session.add(TodoTag(todo_id=todo_id, tag_id=UUID(tid_str)))


# ---------------------------------------------------------------------------
# Field parsers for datetime columns
# ---------------------------------------------------------------------------

_DT_FIELDS_NOTE = {"created_at", "updated_at"}
_DT_FIELDS_TODO = {
    "created_at", "updated_at", "completed_at", "deadline",
    "reminder_at", "recurrence_end_date",
}
_DT_FIELDS_FOLDER = {"created_at", "updated_at"}
_DT_FIELDS_TAG = {"created_at"}


def _make_dt_parser(dt_fields: set[str]) -> dict[str, Any]:
    """Return a field_parsers dict that parses datetime strings for given fields."""
    return {field: _parse_dt for field in dt_fields}


# ---------------------------------------------------------------------------
# Main import function
# ---------------------------------------------------------------------------


async def import_user_data(
    db: AsyncSession,
    user_id: str | UUID,
    data: dict,
) -> dict:
    """Upsert all entities from a backup dict into the database.

    Non-destructive: entities already in DB but not in backup are preserved.
    All changes run in the caller's session/transaction.

    Import order: tags -> folders -> notes -> todos -> junctions

    Args:
        db: Async database session (caller manages transaction).
        user_id: Owning user's UUID.
        data: Parsed backup dict (version, data.{notes,todos,folders,tags}).

    Returns:
        Counts dict: {entity_type: {"created": N, "updated": N, "skipped": N}}
    """
    uid = UUID(str(user_id)) if not isinstance(user_id, UUID) else user_id
    entities = data.get("data", {})

    counts: dict[str, dict[str, int]] = {
        "tags": {"created": 0, "updated": 0, "skipped": 0},
        "folders": {"created": 0, "updated": 0, "skipped": 0},
        "notes": {"created": 0, "updated": 0, "skipped": 0},
        "todos": {"created": 0, "updated": 0, "skipped": 0},
    }

    # -- 1. Tags (no deps) ---------------------------------------------------
    tag_list: list[dict] = entities.get("tags", [])
    valid_tag_ids: set[str] = set()
    for tag_data in tag_list:
        result = await _upsert_entity(
            db, Tag, uid, tag_data,
            field_parsers=_make_dt_parser(_DT_FIELDS_TAG),
        )
        counts["tags"][result] += 1
        if result != "skipped":
            valid_tag_ids.add(tag_data["id"])

    # Also track tag IDs that already existed before this backup
    # (they're valid targets for junction tables too)
    existing_tags = await db.execute(select(Tag.id).where(Tag.user_id == uid))
    for row in existing_tags:
        valid_tag_ids.add(str(row[0]))

    # -- 2. Folders (sorted by depth to handle parent_id self-refs) ----------
    folder_list: list[dict] = entities.get("folders", [])
    sorted_folders = _sort_folders_by_depth(folder_list)
    for folder_data in sorted_folders:
        result = await _upsert_entity(
            db, Folder, uid, folder_data,
            field_parsers=_make_dt_parser(_DT_FIELDS_FOLDER),
        )
        counts["folders"][result] += 1

    # Flush so Note FK constraints resolve against newly inserted folders
    await db.flush()

    # -- 3. Notes (may reference folder_id) ----------------------------------
    note_list: list[dict] = entities.get("notes", [])
    note_tag_map: dict[str, list[str]] = {}
    for note_data in note_list:
        tag_ids = note_data.get("tag_ids", [])
        note_tag_map[note_data["id"]] = tag_ids
        result = await _upsert_entity(
            db, Note, uid, note_data,
            field_parsers=_make_dt_parser(_DT_FIELDS_NOTE),
        )
        counts["notes"][result] += 1

    # Flush so Todo FK constraints resolve against newly inserted notes
    await db.flush()

    # -- 4. Todos (parent_id self-ref, note_id FK) ---------------------------
    # Sort by depth to handle parent_id self-references (same strategy as folders)
    todo_list: list[dict] = entities.get("todos", [])
    sorted_todos = _sort_todos_by_depth(todo_list)
    todo_tag_map: dict[str, list[str]] = {}
    for todo_data in sorted_todos:
        tag_ids = todo_data.get("tag_ids", [])
        todo_tag_map[todo_data["id"]] = tag_ids
        result = await _upsert_entity(
            db, Todo, uid, todo_data,
            field_parsers=_make_dt_parser(_DT_FIELDS_TODO),
        )
        counts["todos"][result] += 1

    # Flush so junction table inserts can reference existing PKs
    await db.flush()

    # -- 5. Junction tables: note_tags, todo_tags ----------------------------
    for note_id_str, tag_ids in note_tag_map.items():
        if tag_ids:
            await _restore_note_tags(
                db, UUID(note_id_str), tag_ids, valid_tag_ids
            )

    for todo_id_str, tag_ids in todo_tag_map.items():
        if tag_ids:
            await _restore_todo_tags(
                db, UUID(todo_id_str), tag_ids, valid_tag_ids
            )

    logger.info(
        "import_user_data: user=%s counts=%s",
        uid, {k: v for k, v in counts.items()},
    )

    return counts


def _sort_todos_by_depth(todos: list[dict]) -> list[dict]:
    """Topological sort for todos with self-referential parent_id."""
    id_to_todo = {t["id"]: t for t in todos}
    ordered: list[dict] = []
    visited: set[str] = set()

    def visit(tid: str, depth: int = 0) -> None:
        if tid in visited or depth > len(todos):
            return
        todo = id_to_todo.get(tid)
        if todo is None:
            return
        parent_id = todo.get("parent_id")
        if parent_id and parent_id in id_to_todo and parent_id not in visited:
            visit(parent_id, depth + 1)
        if tid not in visited:
            visited.add(tid)
            ordered.append(todo)

    for t in todos:
        visit(t["id"])

    for t in todos:
        if t["id"] not in visited:
            ordered.append(t)

    return ordered
