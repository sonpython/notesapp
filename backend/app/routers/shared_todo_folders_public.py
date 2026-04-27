"""Public router for accessing a shared todo folder via pub_id.

All endpoints under `/api/pub/folder/{pub_id}/...` are unauthenticated by
JWT but gated by a short-lived share session cookie issued by /access.

Layout mirrors `shared_notes` public endpoints with extra editable mutations.
"""

from __future__ import annotations

from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.shared_todo_folder import SharedTodoFolder
from app.schemas.shared_todo_folder import (
    SharedFolderTodoCreate,
    SharedFolderTodoReorderRequest,
    SharedFolderTodoResponse,
    SharedFolderTodoToggleRequest,
    SharedFolderTodoUpdate,
    SharedTodoFolderAccessRequest,
    SharedTodoFolderCheckResponse,
    SharedTodoFolderViewResponse,
)
from app.services.share_folder_auth import (
    ShareFolderContext,
    load_share_folder,
    require_editable,
    require_share_session,
)
from app.services.share_session_service import issue_share_session
from app.services.shared_folder_todo_service import (
    create_todo_in_share,
    delete_todo_in_share,
    list_todos_in_share,
    reorder_todos_in_share,
    toggle_todo_in_share,
    update_todo_in_share,
)

router = APIRouter(prefix="/api/pub/folder", tags=["public-todo-folder"])


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# -- Probe + access ---------------------------------------------------------


@router.get(
    "/{pub_id}/check",
    response_model=SharedTodoFolderCheckResponse,
)
async def check_shared_folder(
    share: SharedTodoFolder = Depends(load_share_folder),
) -> SharedTodoFolderCheckResponse:
    """Probe a shared folder. Does not consume a view, does not issue a session."""
    return SharedTodoFolderCheckResponse(
        requires_password=share.password_hash is not None,
        is_editable=share.is_editable,
        folder_name=share.todo_folder.name,
    )


@router.post(
    "/{pub_id}/access",
    response_model=SharedTodoFolderViewResponse,
)
async def access_shared_folder(
    response: Response,
    body: SharedTodoFolderAccessRequest | None = None,
    share: SharedTodoFolder = Depends(load_share_folder),
    db: AsyncSession = Depends(get_db),
) -> SharedTodoFolderViewResponse:
    """Verify password (if any), issue session cookie, return folder + todos.

    Increments view_count exactly once per successful access. Subsequent GETs
    use the session cookie and don't bump the count.
    """
    if share.password_hash:
        if body is None or not body.password:
            raise HTTPException(status_code=401, detail="Password required")
        if not _verify_password(body.password, share.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect password")

    share.view_count += 1
    await db.commit()
    await db.refresh(share)

    issue_share_session(response, share.pub_id, share.is_editable)

    todos = await list_todos_in_share(db, share)
    return SharedTodoFolderViewResponse(
        folder_name=share.todo_folder.name,
        is_editable=share.is_editable,
        todos=[SharedFolderTodoResponse(**t) for t in todos],
    )


# -- Read --------------------------------------------------------------------


@router.get(
    "/{pub_id}/todos",
    response_model=list[SharedFolderTodoResponse],
)
async def list_shared_todos(
    ctx: ShareFolderContext = Depends(require_share_session),
    db: AsyncSession = Depends(get_db),
) -> list[SharedFolderTodoResponse]:
    """Re-fetch todos in the shared folder (idempotent, no view counted)."""
    todos = await list_todos_in_share(db, ctx.share)
    return [SharedFolderTodoResponse(**t) for t in todos]


# -- Mutations (editable mode only) -----------------------------------------


@router.post(
    "/{pub_id}/todos",
    response_model=SharedFolderTodoResponse,
    status_code=201,
)
async def create_shared_todo(
    payload: SharedFolderTodoCreate,
    ctx: ShareFolderContext = Depends(require_editable),
    db: AsyncSession = Depends(get_db),
) -> SharedFolderTodoResponse:
    todo = await create_todo_in_share(db, ctx.share, payload)
    return SharedFolderTodoResponse(**todo)


@router.put(
    "/{pub_id}/todos/reorder",
    status_code=204,
)
async def reorder_shared_todos(
    payload: SharedFolderTodoReorderRequest,
    ctx: ShareFolderContext = Depends(require_editable),
    db: AsyncSession = Depends(get_db),
) -> None:
    await reorder_todos_in_share(db, ctx.share, payload)


@router.put(
    "/{pub_id}/todos/{todo_id}",
    response_model=SharedFolderTodoResponse,
)
async def update_shared_todo(
    payload: SharedFolderTodoUpdate,
    todo_id: UUID = Path(...),
    ctx: ShareFolderContext = Depends(require_editable),
    db: AsyncSession = Depends(get_db),
) -> SharedFolderTodoResponse:
    todo = await update_todo_in_share(db, ctx.share, todo_id, payload)
    return SharedFolderTodoResponse(**todo)


@router.post(
    "/{pub_id}/todos/{todo_id}/toggle",
    response_model=SharedFolderTodoResponse,
)
async def toggle_shared_todo(
    payload: SharedFolderTodoToggleRequest,
    todo_id: UUID = Path(...),
    ctx: ShareFolderContext = Depends(require_editable),
    db: AsyncSession = Depends(get_db),
) -> SharedFolderTodoResponse:
    todo = await toggle_todo_in_share(db, ctx.share, todo_id, payload.expected_updated_at)
    return SharedFolderTodoResponse(**todo)


@router.delete(
    "/{pub_id}/todos/{todo_id}",
    status_code=204,
)
async def delete_shared_todo(
    payload: SharedFolderTodoToggleRequest,
    todo_id: UUID = Path(...),
    ctx: ShareFolderContext = Depends(require_editable),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a todo. Body carries `expected_updated_at` for optimistic lock.

    Using a body on DELETE is technically allowed but rare; if it causes
    proxy issues we can switch to a query param later.
    """
    await delete_todo_in_share(db, ctx.share, todo_id, payload.expected_updated_at)
