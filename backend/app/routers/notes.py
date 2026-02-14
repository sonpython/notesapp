"""Notes router -- CRUD endpoints for user notes."""

from __future__ import annotations

import io
import zipfile
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate
from app.schemas.tag import TagAttachRequest
from app.schemas.pagination import PaginatedResponse
from app.services.note_query_service import build_notes_list_query, apply_note_update
from app.services.note_export_service import (
    export_note_as_markdown,
    export_note_as_pdf,
)
from app.services.tag_service import attach_tags_to_note, detach_tag_from_note

from app.models.note import Note

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("/", response_model=PaginatedResponse[NoteListResponse])
async def list_notes(
    folder_id: UUID | None = Query(None),
    search: str | None = Query(None),
    is_archived: bool | None = Query(None),
    is_pinned: bool | None = Query(None),
    tag_ids: str | None = Query(None, description="Comma-separated tag UUIDs"),
    limit: int = Query(50, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[NoteListResponse]:
    """List notes for the current user with optional filters and pagination."""
    # Parse tag_ids from comma-separated string
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [UUID(tid.strip()) for tid in tag_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag_ids format")

    # Build base query
    base_stmt = build_notes_list_query(
        user_id=user_id,
        folder_id=folder_id,
        search=search,
        is_archived=is_archived,
        is_pinned=is_pinned,
        tag_ids=parsed_tag_ids,
    )

    # Get total count
    count_stmt = select(func.count()).select_from(base_stmt.alias())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Apply pagination
    paginated_stmt = base_stmt.limit(limit).offset(offset)
    result = await session.execute(paginated_stmt)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(
    body: NoteCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """Create a new note for the current user."""
    # Auto-generate title from content if empty
    title = body.title
    if not title and body.content:
        # Use first line or first 50 chars
        first_line = body.content.split('\n')[0].strip()
        title = first_line[:50] + ('...' if len(first_line) > 50 else '')

    note = Note(
        user_id=user_id,
        title=title or 'Untitled',
        content=body.content,
        folder_id=body.folder_id,
        is_pinned=body.is_pinned,
    )
    session.add(note)
    await session.commit()

    # Attach tags if provided
    if body.tag_ids:
        await attach_tags_to_note(session, note.id, body.tag_ids, user_id)
        await session.commit()

    # Reload with eager-loaded tags to avoid lazy loading issues
    result = await session.execute(
        select(Note).where(Note.id == note.id).options(selectinload(Note.tags))
    )
    return result.scalar_one()


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """Get a single note by ID, verifying ownership."""
    # Eager load tags
    result = await session.execute(
        select(Note).where(Note.id == note_id).options(selectinload(Note.tags))
    )
    note = result.scalar_one_or_none()
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
    # Eager load tags to avoid lazy loading issues
    result = await session.execute(
        select(Note).where(Note.id == note_id).options(selectinload(Note.tags))
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    apply_note_update(note, body)
    await session.commit()

    # Reload with eager-loaded tags to avoid lazy loading issues
    result = await session.execute(
        select(Note).where(Note.id == note_id).options(selectinload(Note.tags))
    )
    return result.scalar_one()


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


# -- Tag Management Endpoints -------------------------------------------------


@router.post("/{note_id}/tags", response_model=NoteResponse)
async def add_tags_to_note(
    note_id: UUID,
    body: TagAttachRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NoteResponse:
    """Attach tags to a note."""
    # Verify note exists and belongs to user
    result = await session.execute(
        select(Note).where(Note.id == note_id).options(selectinload(Note.tags))
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Attach tags
    await attach_tags_to_note(session, note_id, body.tag_ids, user_id)
    await session.commit()

    # Reload with eager-loaded tags
    result = await session.execute(
        select(Note).where(Note.id == note_id).options(selectinload(Note.tags))
    )
    return result.scalar_one()


@router.delete("/{note_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_note(
    note_id: UUID,
    tag_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Remove a tag from a note."""
    # Verify note exists and belongs to user
    result = await session.execute(
        select(Note).where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if str(note.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Detach tag
    await detach_tag_from_note(session, note_id, tag_id)
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
