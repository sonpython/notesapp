"""Owner-side router for sharing a todo folder via public link.

Endpoints (auth: JWT Bearer):
  POST   /api/todo-folders/{folder_id}/share   create or update share
  GET    /api/todo-folders/{folder_id}/share   get share info (or 204 None)
  DELETE /api/todo-folders/{folder_id}/share   revoke share
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.shared_note import generate_pub_id
from app.models.shared_todo_folder import SharedTodoFolder
from app.models.todo_folder import TodoFolder
from app.schemas.shared_todo_folder import (
    ShareTodoFolderRequest,
    ShareTodoFolderResponse,
)

router = APIRouter(tags=["shared-todo-folders"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def _load_owned_folder(folder_id: UUID, user_id: str, db: AsyncSession) -> TodoFolder:
    folder = await db.get(TodoFolder, folder_id)
    if folder is None or str(folder.user_id) != user_id:
        # Use 404 for both missing and unauthorized to avoid leaking existence
        raise HTTPException(status_code=404, detail="Todo folder not found")
    return folder


def _to_response(share: SharedTodoFolder) -> ShareTodoFolderResponse:
    return ShareTodoFolderResponse(
        pub_id=share.pub_id,
        url=f"/pub/folder/{share.pub_id}",
        has_password=share.password_hash is not None,
        is_editable=share.is_editable,
        expires_at=share.expires_at,
        max_views=share.max_views,
        view_count=share.view_count,
        created_at=share.created_at,
    )


@router.post(
    "/api/todo-folders/{folder_id}/share",
    response_model=ShareTodoFolderResponse,
)
async def share_todo_folder(
    folder_id: UUID,
    request: ShareTodoFolderRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareTodoFolderResponse:
    """Create or update the share link for a todo folder."""
    await _load_owned_folder(folder_id, user_id, db)

    stmt = select(SharedTodoFolder).where(SharedTodoFolder.todo_folder_id == folder_id)
    share = (await db.execute(stmt)).scalar_one_or_none()

    expires_at = (
        datetime.now(UTC) + timedelta(hours=request.expires_in_hours)
        if request.expires_in_hours
        else None
    )
    password_hash = _hash_password(request.password) if request.password else None

    if share:
        share.password_hash = password_hash
        share.expires_at = expires_at
        share.max_views = request.max_views
        share.is_editable = request.is_editable
        share.view_count = 0
    else:
        # Generate a unique pub_id with retries
        for _ in range(10):
            candidate = generate_pub_id()
            existing = await db.execute(
                select(SharedTodoFolder).where(SharedTodoFolder.pub_id == candidate)
            )
            if existing.scalar_one_or_none() is None:
                break
        else:
            raise HTTPException(status_code=500, detail="Failed to generate unique pub_id")

        share = SharedTodoFolder(
            todo_folder_id=folder_id,
            pub_id=candidate,
            password_hash=password_hash,
            expires_at=expires_at,
            max_views=request.max_views,
            is_editable=request.is_editable,
        )
        db.add(share)

    await db.commit()
    await db.refresh(share)
    return _to_response(share)


@router.get(
    "/api/todo-folders/{folder_id}/share",
    response_model=ShareTodoFolderResponse | None,
)
async def get_todo_folder_share(
    folder_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareTodoFolderResponse | None:
    """Return the share info for a todo folder (null if not shared)."""
    await _load_owned_folder(folder_id, user_id, db)

    stmt = select(SharedTodoFolder).where(SharedTodoFolder.todo_folder_id == folder_id)
    share = (await db.execute(stmt)).scalar_one_or_none()
    if share is None:
        return None
    return _to_response(share)


@router.delete("/api/todo-folders/{folder_id}/share", status_code=204)
async def unshare_todo_folder(
    folder_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove the share link for a todo folder."""
    await _load_owned_folder(folder_id, user_id, db)

    stmt = select(SharedTodoFolder).where(SharedTodoFolder.todo_folder_id == folder_id)
    share = (await db.execute(stmt)).scalar_one_or_none()
    if share is not None:
        await db.delete(share)
        await db.commit()
