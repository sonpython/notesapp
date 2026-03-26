"""Todo folders router -- CRUD endpoints for todo folder organization."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.todo import Todo
from app.models.todo_folder import TodoFolder
from app.schemas.pagination import PaginatedResponse
from app.schemas.todo_folder import (
    TodoFolderCreate,
    TodoFolderResponse,
    TodoFolderStatsResponse,
    TodoFolderUpdate,
)

router = APIRouter(prefix="/api/todo-folders", tags=["todo-folders"])


@router.get("/", response_model=PaginatedResponse[TodoFolderResponse])
async def list_todo_folders(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TodoFolderResponse]:
    """List all todo folders for the current user."""
    count_stmt = select(func.count()).select_from(
        select(TodoFolder).where(TodoFolder.user_id == user_id).subquery()
    )
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(TodoFolder)
        .where(TodoFolder.user_id == user_id)
        .order_by(TodoFolder.sort_order.asc(), TodoFolder.name.asc())
        .limit(limit)
        .offset(offset)
    )
    items = (await session.execute(stmt)).scalars().all()

    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=TodoFolderResponse, status_code=201)
async def create_todo_folder(
    body: TodoFolderCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoFolderResponse:
    """Create a new todo folder."""
    folder = TodoFolder(
        user_id=user_id,
        name=body.name,
        parent_id=body.parent_id,
        sort_order=body.sort_order,
    )
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return folder


@router.put("/{folder_id}", response_model=TodoFolderResponse)
async def update_todo_folder(
    folder_id: UUID,
    body: TodoFolderUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoFolderResponse:
    """Update a todo folder."""
    folder = await session.get(TodoFolder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Todo folder not found")
    if str(folder.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(folder, field, value)

    await session.commit()
    await session.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=204)
async def delete_todo_folder(
    folder_id: UUID,
    cascade: bool = Query(False, description="Also delete all todos in this folder"),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a todo folder. With cascade=true, also deletes all todos in the folder."""
    folder = await session.get(TodoFolder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Todo folder not found")
    if str(folder.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if cascade:
        await session.execute(
            sa_delete(Todo).where(Todo.folder_id == folder_id, Todo.user_id == user_id)
        )

    await session.delete(folder)
    await session.commit()


@router.get("/{folder_id}/stats", response_model=TodoFolderStatsResponse)
async def get_todo_folder_stats(
    folder_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoFolderStatsResponse:
    """Get completion stats for a todo folder (top-level todos only)."""
    folder = await session.get(TodoFolder, folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Todo folder not found")
    if str(folder.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    stmt = select(
        func.count().label("total"),
        func.sum(case((Todo.is_completed == True, 1), else_=0)).label("completed"),
    ).where(
        Todo.folder_id == folder_id,
        Todo.parent_id.is_(None),
    )
    row = (await session.execute(stmt)).one()
    total = row.total or 0
    completed = row.completed or 0

    return TodoFolderStatsResponse(
        folder_id=folder_id,
        total=total,
        completed=completed,
        completion_pct=round((completed / total) * 100) if total > 0 else 0,
    )
