"""Notes router -- CRUD endpoints for user notes."""

from __future__ import annotations

import io
import zipfile
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate
from app.services.note_query_service import build_notes_list_query, apply_note_update
from app.services.note_export_service import (
    export_note_as_markdown,
    export_note_as_pdf,
)

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


# -- Export Endpoints ---------------------------------------------------------


@router.get("/{note_id}/export/md")
async def export_note_markdown(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export a single note as markdown file."""
    note = await session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    markdown_content = export_note_as_markdown(note)
    filename = f"{note.title or 'untitled'}.md".replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(markdown_content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{note_id}/export/pdf")
async def export_note_pdf(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export a single note as PDF file."""
    note = await session.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    pdf_bytes = export_note_as_pdf(note)
    filename = f"{note.title or 'untitled'}.pdf".replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/zip")
async def export_all_notes_zip(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export all user notes as a ZIP file containing markdown files."""
    # Fetch all notes for the user
    stmt = select(Note).where(Note.user_id == user_id).order_by(Note.created_at)
    result = await session.execute(stmt)
    notes = result.scalars().all()

    if not notes:
        raise HTTPException(status_code=404, detail="No notes found")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for note in notes:
            markdown_content = export_note_as_markdown(note)
            filename = f"{note.title or 'untitled'}_{note.id}.md".replace(" ", "_")
            zip_file.writestr(filename, markdown_content)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="notes_export.zip"'},
    )
