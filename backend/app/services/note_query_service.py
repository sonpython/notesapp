"""Query-building helpers for the notes router."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.models.note import Note
from app.models.tag import NoteTag
from app.schemas.note import NoteUpdate


def build_notes_list_query(
    *,
    user_id: str,
    folder_id: UUID | None = None,
    search: str | None = None,
    is_archived: bool | None = None,
    is_pinned: bool | None = None,
    tag_ids: list[UUID] | None = None,
) -> Select:
    """Build a SELECT statement for listing notes with optional filters.

    Uses PostgreSQL full-text search (tsvector/tsquery) for better results.
    Falls back to ilike for very short queries.
    """
    stmt = select(Note).where(Note.user_id == user_id)

    if folder_id is not None:
        stmt = stmt.where(Note.folder_id == folder_id)

    if is_archived is not None:
        stmt = stmt.where(Note.is_archived == is_archived)

    if is_pinned is not None:
        stmt = stmt.where(Note.is_pinned == is_pinned)

    if tag_ids:
        # Filter notes that have ANY of the specified tags (intersection)
        stmt = stmt.where(
            Note.id.in_(
                select(NoteTag.note_id).where(NoteTag.tag_id.in_(tag_ids))
            )
        )

    if search:
        search = search.strip()
        if len(search) < 2:
            # Short queries: fallback to ilike
            pattern = f"%{search}%"
            stmt = stmt.where(
                Note.title.ilike(pattern) | Note.content.ilike(pattern)
            )
        else:
            # Full-text search on title and content
            tsvector = func.to_tsvector(
                'english',
                func.coalesce(Note.title, '') + ' ' + func.coalesce(Note.content, '')
            )
            tsquery = func.plainto_tsquery('english', search)
            stmt = stmt.where(tsvector.op('@@')(tsquery))

    # Eager load tags to avoid N+1 queries
    stmt = stmt.options(selectinload(Note.tags))

    # Pinned notes first, then most recently updated
    stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())

    return stmt


def apply_note_update(note: Note, body: NoteUpdate) -> None:
    """Apply only the fields that were explicitly provided in the update body."""
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
