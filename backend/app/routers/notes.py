"""Notes router -- CRUD endpoints for user notes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate
from app.services.note_query_service import build_notes_list_query, apply_note_update

from app.models.note import Note

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("/", response_model=list[NoteListResponse])
async def list_notes(
    folder_id: UUID | None = Query(None),
    search: str | None = Query(None),
    is_archived: bool | None = Query(None),
    is_pinned: bool | None = Query(None),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[NoteListResponse]:
    """List notes for the current user with optional filters."""
    stmt = build_notes_list_query(
        user_id=user_id,
        folder_id=folder_id,
        search=search,
        is_archived=is_archived,
        is_pinned=is_pinned,
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(
    body: NoteCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """Create a new note for the current user."""
    note = Note(
        user_id=user_id,
        title=body.title,
        content=body.content,
        folder_id=body.folder_id,
        is_pinned=body.is_pinned,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """Get a single note by ID, verifying ownership."""
    note = await session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: UUID,
    body: NoteUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """Partial update of a note -- only provided fields are changed."""
    note = await session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    apply_note_update(note, body)
    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a note by ID."""
    note = await session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await session.delete(note)
    await session.commit()
