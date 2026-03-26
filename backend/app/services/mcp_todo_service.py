"""Database operations for MCP todo tools. Reuses existing SQLAlchemy models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.todo import Todo
from app.models.todo_folder import TodoFolder


async def list_folders(session: AsyncSession, user_id: str) -> list[dict]:
    stmt = (
        select(TodoFolder)
        .where(TodoFolder.user_id == user_id)
        .order_by(TodoFolder.sort_order.asc(), TodoFolder.name.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [_folder_to_dict(f) for f in rows]


async def create_folder(
    session: AsyncSession, user_id: str, name: str, parent_id: str | None = None
) -> dict:
    folder = TodoFolder(user_id=user_id, name=name, parent_id=parent_id)
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return _folder_to_dict(folder)


async def update_folder(
    session: AsyncSession, user_id: str, folder_id: str, **fields: str | None
) -> dict:
    folder = await session.get(TodoFolder, UUID(folder_id))
    if not folder or str(folder.user_id) != user_id:
        raise ValueError(f"Folder {folder_id} not found")
    for k, v in fields.items():
        if v is not None:
            setattr(folder, k, v)
    await session.commit()
    await session.refresh(folder)
    return _folder_to_dict(folder)


async def delete_folder(
    session: AsyncSession, user_id: str, folder_id: str, cascade: bool = False
) -> bool:
    folder = await session.get(TodoFolder, UUID(folder_id))
    if not folder or str(folder.user_id) != user_id:
        raise ValueError(f"Folder {folder_id} not found")
    if cascade:
        from sqlalchemy import delete as sa_delete

        from app.models.todo import Todo

        await session.execute(
            sa_delete(Todo).where(Todo.folder_id == UUID(folder_id), Todo.user_id == user_id)
        )
    await session.delete(folder)
    await session.commit()
    return True


async def list_todos(
    session: AsyncSession,
    user_id: str,
    folder_id: str | None = None,
    is_completed: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    stmt = select(Todo).where(Todo.user_id == user_id, Todo.parent_id.is_(None))
    if folder_id:
        stmt = stmt.where(Todo.folder_id == UUID(folder_id))
    if is_completed is not None:
        stmt = stmt.where(Todo.is_completed == is_completed)
    stmt = (
        stmt.options(selectinload(Todo.children))
        .order_by(Todo.is_completed.asc(), Todo.sort_order.asc(), Todo.created_at.asc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [_todo_to_dict(t) for t in rows]


async def create_todo(
    session: AsyncSession,
    user_id: str,
    title: str,
    folder_id: str | None = None,
    priority: int = 0,
    description: str | None = None,
    deadline: str | None = None,
    parent_id: str | None = None,
) -> dict:
    todo = Todo(
        user_id=user_id,
        title=title,
        folder_id=UUID(folder_id) if folder_id else None,
        priority=priority,
        description=description,
        deadline=datetime.fromisoformat(deadline) if deadline else None,
        parent_id=UUID(parent_id) if parent_id else None,
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return _todo_to_dict(todo)


async def update_todo(
    session: AsyncSession, user_id: str, todo_id: str, **fields: str | int | bool | None
) -> dict:
    todo = await session.get(Todo, UUID(todo_id))
    if not todo or str(todo.user_id) != user_id:
        raise ValueError(f"Todo {todo_id} not found")
    for k, v in fields.items():
        if v is not None:
            setattr(todo, k, v)
    await session.commit()
    await session.refresh(todo)
    return _todo_to_dict(todo)


async def delete_todo(session: AsyncSession, user_id: str, todo_id: str) -> bool:
    todo = await session.get(Todo, UUID(todo_id))
    if not todo or str(todo.user_id) != user_id:
        raise ValueError(f"Todo {todo_id} not found")
    await session.delete(todo)
    await session.commit()
    return True


async def toggle_todo(session: AsyncSession, user_id: str, todo_id: str) -> dict:
    todo = await session.get(Todo, UUID(todo_id))
    if not todo or str(todo.user_id) != user_id:
        raise ValueError(f"Todo {todo_id} not found")
    todo.is_completed = not todo.is_completed
    todo.completed_at = datetime.now(UTC) if todo.is_completed else None
    await session.commit()
    await session.refresh(todo)
    return _todo_to_dict(todo)


async def get_folder_stats(session: AsyncSession, user_id: str, folder_id: str) -> dict:
    folder = await session.get(TodoFolder, UUID(folder_id))
    if not folder or str(folder.user_id) != user_id:
        raise ValueError(f"Folder {folder_id} not found")
    stmt = select(
        func.count().label("total"),
        func.sum(case((Todo.is_completed == True, 1), else_=0)).label("completed"),
    ).where(Todo.folder_id == UUID(folder_id), Todo.parent_id.is_(None))
    row = (await session.execute(stmt)).one()
    total = row.total or 0
    completed = row.completed or 0
    return {
        "folder_id": folder_id,
        "folder_name": folder.name,
        "total": total,
        "completed": completed,
        "active": total - completed,
        "completion_pct": round((completed / total) * 100) if total > 0 else 0,
    }


def _folder_to_dict(f: TodoFolder) -> dict:
    return {
        "id": str(f.id),
        "name": f.name,
        "parent_id": str(f.parent_id) if f.parent_id else None,
        "sort_order": f.sort_order,
        "created_at": f.created_at.isoformat(),
    }


def _todo_to_dict(t: Todo) -> dict:
    d = {
        "id": str(t.id),
        "title": t.title,
        "description": t.description,
        "is_completed": t.is_completed,
        "priority": t.priority,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "folder_id": str(t.folder_id) if t.folder_id else None,
        "parent_id": str(t.parent_id) if t.parent_id else None,
        "created_at": t.created_at.isoformat(),
    }
    # Only include children stats if already eagerly loaded (avoid lazy load)
    from sqlalchemy import inspect as sa_inspect

    if "children" in sa_inspect(t).dict:
        children = t.children
        if children:
            d["children_count"] = len(children)
            d["children_completed"] = sum(1 for c in children if c.is_completed)
    return d
