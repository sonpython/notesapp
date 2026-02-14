"""Todos router -- CRUD and toggle endpoints for todo items."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate, TodoWithChildrenResponse
from app.services.todo_query_service import build_todos_list_query, toggle_todo_completion

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
async def list_todos(
    is_completed: bool | None = Query(None),
    priority: int | None = Query(None),
    has_deadline: bool | None = Query(None),
    note_id: UUID | None = Query(None),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[TodoResponse]:
    """List top-level todos for the current user with optional filters."""
    stmt = build_todos_list_query(
        user_id=user_id,
        is_completed=is_completed,
        priority=priority,
        has_deadline=has_deadline,
        note_id=note_id,
    )
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=TodoResponse, status_code=201)
async def create_todo(
    body: TodoCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """Create a new todo for the current user."""
    todo = Todo(
        user_id=user_id,
        title=body.title,
        description=body.description,
        deadline=body.deadline,
        parent_id=body.parent_id,
        note_id=body.note_id,
        priority=body.priority,
        sort_order=body.sort_order,
        reminder_at=body.reminder_at,
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


@router.get("/{todo_id}", response_model=TodoWithChildrenResponse)
async def get_todo(
    todo_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoWithChildrenResponse:
    """Get a single todo with its children, verifying ownership."""
    stmt = (
        select(Todo)
        .where(Todo.id == todo_id)
        .options(selectinload(Todo.children))
    )
    result = await session.execute(stmt)
    todo = result.scalar_one_or_none()

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID,
    body: TodoUpdate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """Partial update of a todo -- only provided fields are changed."""
    todo = await session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    await session.commit()
    await session.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a todo by ID (cascades to children)."""
    todo = await session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await session.delete(todo)
    await session.commit()


@router.post("/{todo_id}/toggle", response_model=TodoResponse)
async def toggle_todo(
    todo_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """Toggle is_completed and set/clear completed_at accordingly."""
    todo = await session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    toggle_todo_completion(todo)
    await session.commit()
    await session.refresh(todo)
    return todo
