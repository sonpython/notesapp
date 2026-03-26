"""MCP server for NotesApp Todos — exposes todo/folder CRUD as MCP tools.

Authentication: API key via NOTESAPP_API_KEY env var.
Generate keys in NotesApp Settings > API Keys.

Claude Desktop config:
  {
    "mcpServers": {
      "notesapp-todos": {
        "command": "uv",
        "args": ["run", "python", "mcp_server.py"],
        "cwd": "/path/to/backend",
        "env": {
          "NOTESAPP_API_KEY": "na_xxxxxxxx...",
          "DATABASE_URL": "postgresql+asyncpg://..."
        }
      }
    }
  }
"""

import hashlib
import os
import sys
from datetime import UTC, datetime

from fastmcp import FastMCP

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import async_session_factory  # noqa: E402
from app.models.api_key import ApiKey  # noqa: E402
from app.services import mcp_todo_service as svc  # noqa: E402

mcp = FastMCP("NotesApp Todos")

NOTESAPP_API_KEY = os.environ.get("NOTESAPP_API_KEY", "")

# Cache resolved user_id to avoid DB lookup on every tool call
_cached_user_id: str | None = None


async def _resolve_user_id() -> str:
    """Validate API key and return the associated user_id."""
    global _cached_user_id
    if _cached_user_id:
        return _cached_user_id

    if not NOTESAPP_API_KEY:
        raise ValueError(
            "NOTESAPP_API_KEY env var is required. Generate one in NotesApp Settings > API Keys."
        )

    key_hash = hashlib.sha256(NOTESAPP_API_KEY.encode()).hexdigest()

    from sqlalchemy import select

    async with async_session_factory() as session:
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await session.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key is None:
            raise ValueError("Invalid API key. Check NOTESAPP_API_KEY value.")

        # Check expiry
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            raise ValueError("API key has expired. Generate a new one in Settings.")

        # Update last_used_at
        api_key.last_used_at = datetime.now(UTC)
        await session.commit()

        _cached_user_id = str(api_key.user_id)
        return _cached_user_id


# -- Folder tools --


@mcp.tool()
async def list_todo_folders() -> list[dict]:
    """List all todo folders for the current user."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.list_folders(session, uid)


@mcp.tool()
async def create_todo_folder(name: str, parent_id: str | None = None) -> dict:
    """Create a new todo folder. Use parent_id to nest under another folder."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.create_folder(session, uid, name, parent_id)


@mcp.tool()
async def update_todo_folder(
    folder_id: str, name: str | None = None, parent_id: str | None = None
) -> dict:
    """Update a todo folder's name or parent."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.update_folder(session, uid, folder_id, name=name, parent_id=parent_id)


@mcp.tool()
async def delete_todo_folder(folder_id: str) -> bool:
    """Delete a todo folder. Todos in this folder will have their folder_id set to null."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.delete_folder(session, uid, folder_id)


# -- Todo tools --


@mcp.tool()
async def list_todos(
    folder_id: str | None = None,
    is_completed: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    """List todos. Optionally filter by folder_id and completion status."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.list_todos(session, uid, folder_id, is_completed, limit)


@mcp.tool()
async def create_todo(
    title: str,
    folder_id: str | None = None,
    priority: int = 0,
    description: str | None = None,
    deadline: str | None = None,
    parent_id: str | None = None,
) -> dict:
    """Create a new todo. Priority: 0=none, 1=low, 2=medium, 3=high. Deadline: ISO 8601."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.create_todo(
            session, uid, title, folder_id, priority, description, deadline, parent_id
        )


@mcp.tool()
async def update_todo(
    todo_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    folder_id: str | None = None,
) -> dict:
    """Update a todo's fields. Only provided fields are changed."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.update_todo(
            session,
            uid,
            todo_id,
            title=title,
            description=description,
            priority=priority,
            folder_id=folder_id,
        )


@mcp.tool()
async def delete_todo(todo_id: str) -> bool:
    """Delete a todo and all its subtasks."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.delete_todo(session, uid, todo_id)


@mcp.tool()
async def toggle_todo(todo_id: str) -> dict:
    """Toggle a todo's completion status."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.toggle_todo(session, uid, todo_id)


@mcp.tool()
async def get_folder_stats(folder_id: str) -> dict:
    """Get completion statistics for a todo folder."""
    uid = await _resolve_user_id()
    async with async_session_factory() as session:
        return await svc.get_folder_stats(session, uid, folder_id)


if __name__ == "__main__":
    mcp.run()
