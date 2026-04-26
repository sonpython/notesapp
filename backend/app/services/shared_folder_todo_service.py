"""Business logic for public CRUD on todos within a shared folder.

Boundary rules enforced here (NOT in the router) so we never trust the
client to scope itself:
- Only top-level todos (parent_id IS NULL) of the shared folder are visible
- Created todos are forced into the shared folder under the owner's user_id
- Updates/deletes only succeed if the todo currently belongs to the shared folder
- Optimistic locking via expected_updated_at on update/toggle/delete
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shared_todo_folder import SharedTodoFolder
from app.models.todo import Todo
from app.schemas.shared_todo_folder import (
    SharedFolderTodoCreate,
    SharedFolderTodoReorderRequest,
    SharedFolderTodoUpdate,
)


async def list_todos_in_share(db: AsyncSession, share: SharedTodoFolder) -> list[Todo]:
    """Return top-level todos directly inside the shared folder, ordered."""
    stmt = (
        select(Todo)
        .where(
            Todo.folder_id == share.todo_folder_id,
            Todo.parent_id.is_(None),
        )
        .order_by(Todo.sort_order.asc(), Todo.created_at.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def create_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    payload: SharedFolderTodoCreate,
) -> Todo:
    """Create a todo within the shared folder.

    Forces folder_id and user_id; ignores any client-provided foreign keys.
    """
    todo = Todo(
        user_id=share.todo_folder.user_id,
        folder_id=share.todo_folder_id,
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        priority=payload.priority,
        sort_order=payload.sort_order,
    )
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


async def _load_todo_in_share(db: AsyncSession, share: SharedTodoFolder, todo_id: UUID) -> Todo:
    """Fetch a todo and verify it currently belongs to the shared folder.

    Returns 404 if missing OR if it is in a different folder. We use 404 to
    avoid leaking the existence of unrelated todos.
    """
    stmt = select(Todo).where(Todo.id == todo_id)
    todo = (await db.execute(stmt)).scalar_one_or_none()
    if todo is None or todo.folder_id != share.todo_folder_id:
        raise HTTPException(status_code=404, detail="Todo not found in this folder")
    return todo


async def update_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    todo_id: UUID,
    payload: SharedFolderTodoUpdate,
) -> Todo:
    """Optimistically update a todo. Raises 409 on stale token, 404 if absent."""
    todo = await _load_todo_in_share(db, share, todo_id)
    expected = payload.expected_updated_at

    update_data = payload.model_dump(exclude_unset=True, exclude={"expected_updated_at"})
    if not update_data:
        return todo

    # Auto-manage completed_at when toggling via update
    if "is_completed" in update_data:
        if update_data["is_completed"]:
            update_data.setdefault("completed_at", datetime.now(UTC))
        else:
            update_data["completed_at"] = None

    stmt = (
        update(Todo)
        .where(
            Todo.id == todo_id,
            Todo.folder_id == share.todo_folder_id,
            Todo.updated_at == expected,
        )
        .values(**update_data)
        .returning(Todo)
    )
    result = await db.execute(stmt)
    updated = result.scalar_one_or_none()
    if updated is None:
        # Either the row disappeared or updated_at moved on
        await db.rollback()
        raise HTTPException(status_code=409, detail="Todo was modified by someone else")
    await db.commit()
    await db.refresh(updated)
    return updated


async def toggle_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    todo_id: UUID,
    expected_updated_at: datetime,
) -> Todo:
    """Optimistic toggle of is_completed."""
    todo = await _load_todo_in_share(db, share, todo_id)
    new_completed = not todo.is_completed
    new_completed_at = datetime.now(UTC) if new_completed else None

    stmt = (
        update(Todo)
        .where(
            Todo.id == todo_id,
            Todo.folder_id == share.todo_folder_id,
            Todo.updated_at == expected_updated_at,
        )
        .values(is_completed=new_completed, completed_at=new_completed_at)
        .returning(Todo)
    )
    result = await db.execute(stmt)
    updated = result.scalar_one_or_none()
    if updated is None:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Todo was modified by someone else")
    await db.commit()
    await db.refresh(updated)
    return updated


async def delete_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    todo_id: UUID,
    expected_updated_at: datetime,
) -> None:
    """Optimistic delete. 409 if updated_at moved on; 404 if not in this folder."""
    todo = await _load_todo_in_share(db, share, todo_id)
    if todo.updated_at != expected_updated_at:
        raise HTTPException(status_code=409, detail="Todo was modified by someone else")
    await db.delete(todo)
    await db.commit()


async def reorder_todos_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    payload: SharedFolderTodoReorderRequest,
) -> None:
    """Batch-update sort_order for todos within the shared folder only.

    Reorder is intentionally last-write-wins (no optimistic lock per item)
    because it's a low-stakes positional update and per-item locks would
    push the UI into refresh storms during normal drag-drop.
    """
    if not payload.items:
        return
    ids = [item.id for item in payload.items]
    stmt = select(Todo.id, Todo.folder_id).where(Todo.id.in_(ids))
    rows = (await db.execute(stmt)).all()

    folder_ids = {row.folder_id for row in rows}
    if any(fid != share.todo_folder_id for fid in folder_ids) or len(rows) != len(ids):
        # Reject if any item is missing or escaped the shared folder
        raise HTTPException(status_code=400, detail="Invalid todo ids in reorder request")

    for item in payload.items:
        await db.execute(
            update(Todo)
            .where(Todo.id == item.id, Todo.folder_id == share.todo_folder_id)
            .values(sort_order=item.sort_order)
        )
    await db.commit()
