"""Router for public note sharing functionality."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.note import Note
from app.models.shared_note import SharedNote, generate_pub_id
from app.schemas.shared_note import (
    SharedNotePasswordRequest,
    SharedNoteViewResponse,
    ShareNoteRequest,
    ShareNoteResponse,
)
from app.services.minio_storage_service import minio_service

router = APIRouter(tags=["shared"])


def _hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


@router.post("/api/notes/{note_id}/share", response_model=ShareNoteResponse)
async def share_note(
    note_id: UUID,
    request: ShareNoteRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareNoteResponse:
    """Create or update a share link for a note."""
    # Verify note ownership
    stmt = select(Note).where(Note.id == note_id, Note.user_id == UUID(user_id))
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Check if already shared
    stmt = select(SharedNote).where(SharedNote.note_id == note_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    # Calculate expiry
    expires_at = None
    if request.expires_in_hours:
        expires_at = datetime.now(UTC) + timedelta(hours=request.expires_in_hours)

    # Hash password if provided
    password_hash = _hash_password(request.password) if request.password else None

    if shared:
        # Update existing share
        shared.password_hash = password_hash
        shared.expires_at = expires_at
        shared.max_views = request.max_views
        # Reset view count on update
        shared.view_count = 0
    else:
        # Create new share with unique pub_id
        for _ in range(10):  # Max retries for unique ID
            pub_id = generate_pub_id()
            existing = await db.execute(select(SharedNote).where(SharedNote.pub_id == pub_id))
            if not existing.scalar_one_or_none():
                break
        else:
            raise HTTPException(status_code=500, detail="Failed to generate unique ID")

        shared = SharedNote(
            note_id=note_id,
            pub_id=pub_id,
            password_hash=password_hash,
            expires_at=expires_at,
            max_views=request.max_views,
        )
        db.add(shared)

    await db.commit()
    await db.refresh(shared)

    return ShareNoteResponse(
        pub_id=shared.pub_id,
        url=f"/pub/{shared.pub_id}",
        has_password=shared.password_hash is not None,
        expires_at=shared.expires_at,
        max_views=shared.max_views,
        view_count=shared.view_count,
        created_at=shared.created_at,
    )


@router.get("/api/notes/{note_id}/share", response_model=ShareNoteResponse | None)
async def get_share_info(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareNoteResponse | None:
    """Get share info for a note (returns null if not shared)."""
    # Verify note ownership
    stmt = select(Note).where(Note.id == note_id, Note.user_id == UUID(user_id))
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Note not found")

    stmt = select(SharedNote).where(SharedNote.note_id == note_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    if not shared:
        return None

    return ShareNoteResponse(
        pub_id=shared.pub_id,
        url=f"/pub/{shared.pub_id}",
        has_password=shared.password_hash is not None,
        expires_at=shared.expires_at,
        max_views=shared.max_views,
        view_count=shared.view_count,
        created_at=shared.created_at,
    )


@router.delete("/api/notes/{note_id}/share", status_code=204)
async def unshare_note(
    note_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove share link for a note."""
    # Verify note ownership
    stmt = select(Note).where(Note.id == note_id, Note.user_id == UUID(user_id))
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Note not found")

    stmt = select(SharedNote).where(SharedNote.note_id == note_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    if shared:
        await db.delete(shared)
        await db.commit()


@router.get("/api/pub/{pub_id}/check")
async def check_shared_note(
    pub_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check if shared note exists and requires password."""
    stmt = select(SharedNote).where(SharedNote.pub_id == pub_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared note not found")

    # Check expiry
    if shared.expires_at and datetime.now(UTC) > shared.expires_at:
        raise HTTPException(status_code=410, detail="This shared note has expired")

    # Check view limit
    if shared.max_views and shared.view_count >= shared.max_views:
        raise HTTPException(status_code=410, detail="This shared note has reached its view limit")

    return {"requires_password": shared.password_hash is not None}


@router.post("/api/pub/{pub_id}/view", response_model=SharedNoteViewResponse)
async def view_shared_note(
    pub_id: str,
    password_request: SharedNotePasswordRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> SharedNoteViewResponse:
    """View a shared note (increments view count)."""
    stmt = select(SharedNote).where(SharedNote.pub_id == pub_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared note not found")

    # Check expiry
    if shared.expires_at and datetime.now(UTC) > shared.expires_at:
        raise HTTPException(status_code=410, detail="This shared note has expired")

    # Check view limit
    if shared.max_views and shared.view_count >= shared.max_views:
        raise HTTPException(status_code=410, detail="This shared note has reached its view limit")

    # Check password
    if shared.password_hash:
        if not password_request or not password_request.password:
            raise HTTPException(status_code=401, detail="Password required")
        if not _verify_password(password_request.password, shared.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password")

    # Increment view count
    shared.view_count += 1
    await db.commit()

    note = shared.note
    return SharedNoteViewResponse(
        title=note.title,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.post("/api/pub/{pub_id}/import", status_code=201)
async def import_shared_note(
    pub_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Import a shared note to the user's notes."""
    stmt = select(SharedNote).where(SharedNote.pub_id == pub_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared note not found")

    # Check expiry
    if shared.expires_at and datetime.now(UTC) > shared.expires_at:
        raise HTTPException(status_code=410, detail="This shared note has expired")

    # Check view limit
    if shared.max_views and shared.view_count >= shared.max_views:
        raise HTTPException(status_code=410, detail="This shared note has reached its view limit")

    # Create a copy of the note for the user
    original = shared.note
    new_note = Note(
        user_id=UUID(user_id),
        title=f"{original.title} (imported)",
        content=original.content,
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return {"id": str(new_note.id), "title": new_note.title}


@router.get("/api/pub/{pub_id}/image/{image_id}")
async def get_shared_image(
    pub_id: str,
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Serve an image from a shared note (no auth required)."""
    # Find the shared note
    stmt = select(SharedNote).where(SharedNote.pub_id == pub_id)
    result = await db.execute(stmt)
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared note not found")

    # Check expiry
    if shared.expires_at and datetime.now(UTC) > shared.expires_at:
        raise HTTPException(status_code=410, detail="This shared note has expired")

    # Check view limit
    if shared.max_views and shared.view_count > shared.max_views:
        raise HTTPException(status_code=410, detail="This shared note has reached its view limit")

    # Get the note owner's user_id
    note = shared.note
    user_id = str(note.user_id)

    # Find the image in MinIO
    object_key = await minio_service.find_user_image(user_id, image_id)

    if not object_key:
        raise HTTPException(status_code=404, detail="Image not found")

    # Get metadata for content-type
    info = await minio_service.get_image_info(object_key)
    if not info:
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = info.get("content_type", "application/octet-stream")

    # Stream the image with caching
    return StreamingResponse(
        minio_service.get_image(object_key),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600",  # 1 hour cache for public images
        },
    )
