"""Todos router -- CRUD and toggle endpoints for todo items."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.todo import Todo
from app.schemas.pagination import PaginatedResponse
from app.schemas.tag import TagAttachRequest
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate, TodoWithChildrenResponse
from app.services.recurrence_service import create_next_occurrence
from app.services.tag_service import attach_tags_to_todo, detach_tag_from_todo
from app.services.todo_query_service import build_todos_list_query, toggle_todo_completion

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("/", response_model=PaginatedResponse[TodoWithChildrenResponse])
async def list_todos(
    is_completed: bool | None = Query(None),
    priority: int | None = Query(None),
    has_deadline: bool | None = Query(None),
    overdue: bool | None = Query(None, description="Filter overdue todos"),
    note_id: UUID | None = Query(None),
    is_recurring: bool | None = Query(None),
    tag_ids: str | None = Query(None, description="Comma-separated tag UUIDs"),
    limit: int = Query(50, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TodoWithChildrenResponse]:
    """List top-level todos for the current user with optional filters and pagination."""
    # Parse tag_ids from comma-separated string
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [UUID(tid.strip()) for tid in tag_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag_ids format")

    # Build base query
    base_stmt = build_todos_list_query(
        user_id=user_id,
        is_completed=is_completed,
        priority=priority,
        has_deadline=has_deadline,
        overdue=overdue,
        note_id=note_id,
        is_recurring=is_recurring,
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


@router.get("/counts")
async def get_todo_counts(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Get todo counts for sidebar display.

    Returns:
        { total: int, active: int, completed: int }
    """
    uid = UUID(user_id)

    # Total count (top-level only)
    total_result = await session.execute(
        select(func.count()).where(Todo.user_id == uid, Todo.parent_id.is_(None))
    )
    total = total_result.scalar_one()

    # Active count (not completed)
    active_result = await session.execute(
        select(func.count()).where(
            Todo.user_id == uid, Todo.parent_id.is_(None), Todo.is_completed == False
        )
    )
    active = active_result.scalar_one()

    return {
        "total": total,
        "active": active,
        "completed": total - active,
    }


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
        recurrence_type=body.recurrence_type,
        recurrence_interval=body.recurrence_interval,
        recurrence_days=body.recurrence_days,
        recurrence_end_date=body.recurrence_end_date,
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo, ["tags"])

    # Attach tags if provided
    if body.tag_ids:
        await attach_tags_to_todo(session, todo.id, body.tag_ids, user_id)
        await session.commit()
        await session.refresh(todo, ["tags"])

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
        .options(selectinload(Todo.children), selectinload(Todo.tags))
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
    # Eager load tags
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.tags))
    )
    todo = result.scalar_one_or_none()
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
    """Toggle is_completed and set/clear completed_at accordingly.

    If completing a recurring todo, automatically creates next occurrence.
    """
    # Eager load tags
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.tags))
    )
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    toggle_todo_completion(todo)

    # Auto-create next occurrence if completing a recurring todo
    if todo.is_completed and todo.recurrence_type:
        await create_next_occurrence(todo, session)

    await session.commit()

    # Reload with eager-loaded tags to avoid lazy loading issues
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.tags))
    )
    return result.scalar_one()


# -- Tag Management Endpoints -------------------------------------------------


@router.post("/{todo_id}/tags", response_model=TodoResponse)
async def add_tags_to_todo(
    todo_id: UUID,
    body: TagAttachRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """Attach tags to a todo."""
    # Verify todo exists and belongs to user
    result = await session.execute(
        select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.tags))
    )
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Attach tags
    await attach_tags_to_todo(session, todo_id, body.tag_ids, user_id)
    await session.commit()
    await session.refresh(todo, ["tags"])

    return todo


@router.delete("/{todo_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_todo(
    todo_id: UUID,
    tag_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Remove a tag from a todo."""
    # Verify todo exists and belongs to user
    result = await session.execute(select(Todo).where(Todo.id == todo_id))
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if str(todo.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Detach tag
    await detach_tag_from_todo(session, todo_id, tag_id)
    await session.commit()
