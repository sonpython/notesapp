"""Business logic for public CRUD on todos within a shared folder.

Boundary rules enforced here (NOT in the router) so we never trust the
client to scope itself:
- Top-level todos belong to the shared folder when folder_id matches
- Subtasks belong to the shared folder when their root ancestor's folder_id matches
- Created todos are forced into the shared folder under the owner's user_id
  (subtasks inherit the same folder_id so the boundary stays uniform)
- Optimistic locking via expected_updated_at on update / toggle / delete
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


def _todo_to_dict(t: Todo, children_by_parent: dict[UUID, list[Todo]]) -> dict:
    """Recursively materialize a Todo + its descendants into a plain dict.

    Building dicts in pure Python avoids triggering ORM lazy-loads when
    Pydantic later serializes the response (which previously caused
    MissingGreenlet errors past the eager-load depth).
    """
    return {
        "id": t.id,
        "parent_id": t.parent_id,
        "title": t.title,
        "description": t.description,
        "is_completed": t.is_completed,
        "completed_at": t.completed_at,
        "deadline": t.deadline,
        "priority": t.priority,
        "sort_order": t.sort_order,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "children": [
            _todo_to_dict(child, children_by_parent)
            for child in sorted(
                children_by_parent.get(t.id, []),
                key=lambda c: (c.sort_order, c.created_at),
            )
        ],
    }


async def list_todos_in_share(db: AsyncSession, share: SharedTodoFolder) -> list[dict]:
    """Return top-level todos with full subtree as plain dicts.

    One round trip per depth level via two queries (top-level + descendants by
    parent_id IN (...) BFS). No lazy loads on the SQLAlchemy session.
    """
    top_stmt = (
        select(Todo)
        .where(
            Todo.folder_id == share.todo_folder_id,
            Todo.parent_id.is_(None),
        )
        .order_by(Todo.sort_order.asc(), Todo.created_at.asc())
    )
    top_level = list((await db.execute(top_stmt)).scalars().all())

    children_by_parent: dict[UUID, list[Todo]] = {}
    frontier_ids = {t.id for t in top_level}
    while frontier_ids:
        rows = list(
            (await db.execute(select(Todo).where(Todo.parent_id.in_(frontier_ids)))).scalars().all()
        )
        if not rows:
            break
        next_frontier: set[UUID] = set()
        for child in rows:
            children_by_parent.setdefault(child.parent_id, []).append(child)
            next_frontier.add(child.id)
        frontier_ids = next_frontier

    return [_todo_to_dict(t, children_by_parent) for t in top_level]


async def _todo_to_dict_with_subtree(db: AsyncSession, todo: Todo) -> dict:
    """Build a single todo's dict including its descendants."""
    children_by_parent: dict[UUID, list[Todo]] = {}
    frontier_ids: set[UUID] = {todo.id}
    while frontier_ids:
        rows = list(
            (await db.execute(select(Todo).where(Todo.parent_id.in_(frontier_ids)))).scalars().all()
        )
        if not rows:
            break
        next_frontier: set[UUID] = set()
        for child in rows:
            children_by_parent.setdefault(child.parent_id, []).append(child)
            next_frontier.add(child.id)
        frontier_ids = next_frontier
    return _todo_to_dict(todo, children_by_parent)


async def _allowed_todo_ids(db: AsyncSession, share: SharedTodoFolder) -> set[UUID]:
    """All todo ids that count as 'inside' the shared folder.

    Includes top-level todos (folder_id matches) and every descendant in the
    parent chain. Used to authorize mutations on subtasks even when the
    subtask's own folder_id is null (legacy data) or unset.
    """
    top_level = await db.execute(
        select(Todo.id).where(
            Todo.folder_id == share.todo_folder_id,
            Todo.parent_id.is_(None),
        )
    )
    ids: set[UUID] = set(top_level.scalars().all())
    if not ids:
        return ids

    frontier = ids.copy()
    while frontier:
        children = await db.execute(select(Todo.id).where(Todo.parent_id.in_(frontier)))
        new_ids = set(children.scalars().all()) - ids
        if not new_ids:
            break
        ids.update(new_ids)
        frontier = new_ids
    return ids


async def _ensure_in_share(db: AsyncSession, share: SharedTodoFolder, todo_id: UUID) -> Todo:
    """Fetch a todo and verify it currently belongs to the shared folder."""
    allowed = await _allowed_todo_ids(db, share)
    if todo_id not in allowed:
        raise HTTPException(status_code=404, detail="Todo not found in this folder")
    todo = await db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found in this folder")
    return todo


async def create_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    payload: SharedFolderTodoCreate,
) -> dict:
    """Create a todo in the shared folder; supports subtasks via parent_id.

    Forces folder_id and user_id; ignores any client-provided foreign keys
    other than parent_id, which is validated against the allowed-set so we
    cannot create a subtask under an unrelated todo.
    """
    if payload.parent_id is not None:
        allowed = await _allowed_todo_ids(db, share)
        if payload.parent_id not in allowed:
            raise HTTPException(status_code=400, detail="Invalid parent todo")

    todo = Todo(
        user_id=share.todo_folder.user_id,
        folder_id=share.todo_folder_id,
        parent_id=payload.parent_id,
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        priority=payload.priority,
        sort_order=payload.sort_order,
    )
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return await _todo_to_dict_with_subtree(db, todo)


async def update_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    todo_id: UUID,
    payload: SharedFolderTodoUpdate,
) -> dict:
    """Optimistically update a todo. Raises 409 on stale token, 404 if absent."""
    todo = await _ensure_in_share(db, share, todo_id)
    expected = payload.expected_updated_at

    update_data = payload.model_dump(exclude_unset=True, exclude={"expected_updated_at"})
    if not update_data:
        return await _todo_to_dict_with_subtree(db, todo)

    if "is_completed" in update_data:
        if update_data["is_completed"]:
            update_data.setdefault("completed_at", datetime.now(UTC))
        else:
            update_data["completed_at"] = None

    stmt = (
        update(Todo)
        .where(Todo.id == todo_id, Todo.updated_at == expected)
        .values(**update_data)
        .returning(Todo)
    )
    result = await db.execute(stmt)
    updated = result.scalar_one_or_none()
    if updated is None:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Todo was modified by someone else")
    await db.commit()
    await db.refresh(updated)
    return await _todo_to_dict_with_subtree(db, updated)


async def toggle_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    todo_id: UUID,
    expected_updated_at: datetime,
) -> dict:
    """Optimistic toggle of is_completed."""
    todo = await _ensure_in_share(db, share, todo_id)
    new_completed = not todo.is_completed
    new_completed_at = datetime.now(UTC) if new_completed else None

    stmt = (
        update(Todo)
        .where(Todo.id == todo_id, Todo.updated_at == expected_updated_at)
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
    return await _todo_to_dict_with_subtree(db, updated)


async def delete_todo_in_share(
    db: AsyncSession,
    share: SharedTodoFolder,
    todo_id: UUID,
    expected_updated_at: datetime,
) -> None:
    """Optimistic delete. 409 if updated_at moved on; 404 if not in this folder."""
    todo = await _ensure_in_share(db, share, todo_id)
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

    Reorder is intentionally last-write-wins (no optimistic lock per item).
    Accepts both top-level todos and subtasks via the allowed-set check.
    """
    if not payload.items:
        return

    allowed = await _allowed_todo_ids(db, share)
    ids = {item.id for item in payload.items}
    if not ids.issubset(allowed):
        raise HTTPException(status_code=400, detail="Invalid todo ids in reorder request")

    for item in payload.items:
        await db.execute(update(Todo).where(Todo.id == item.id).values(sort_order=item.sort_order))
    await db.commit()
