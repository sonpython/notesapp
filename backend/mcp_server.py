"""MCP server for NotesApp Todos — exposes todo/folder CRUD as MCP tools.

Usage:
  NOTESAPP_USER_ID=<uuid> DATABASE_URL=<url> python mcp_server.py

Claude Desktop config:
  {
    "mcpServers": {
      "notesapp-todos": {
        "command": "uv",
        "args": ["run", "python", "mcp_server.py"],
        "cwd": "/path/to/backend",
        "env": {
          "NOTESAPP_USER_ID": "<user-uuid>",
          "DATABASE_URL": "postgresql+asyncpg://..."
        }
      }
    }
  }
"""

import os
import sys

from fastmcp import FastMCP

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import async_session_factory  # noqa: E402
from app.services import mcp_todo_service as svc  # noqa: E402

mcp = FastMCP("NotesApp Todos")

USER_ID = os.environ.get("NOTESAPP_USER_ID", "")


def _require_user_id() -> str:
    if not USER_ID:
        raise ValueError("NOTESAPP_USER_ID env var is required")
    return USER_ID


# -- Folder tools --


@mcp.tool()
async def list_todo_folders() -> list[dict]:
    """List all todo folders for the current user."""
    uid = _require_user_id()
    async with async_session_factory() as session:
        return await svc.list_folders(session, uid)


@mcp.tool()
async def create_todo_folder(name: str, parent_id: str | None = None) -> dict:
    """Create a new todo folder. Use parent_id to nest under another folder."""
    uid = _require_user_id()
    async with async_session_factory() as session:
        return await svc.create_folder(session, uid, name, parent_id)


@mcp.tool()
async def update_todo_folder(
    folder_id: str, name: str | None = None, parent_id: str | None = None
) -> dict:
    """Update a todo folder's name or parent."""
    uid = _require_user_id()
    async with async_session_factory() as session:
        return await svc.update_folder(session, uid, folder_id, name=name, parent_id=parent_id)


@mcp.tool()
async def delete_todo_folder(folder_id: str) -> bool:
    """Delete a todo folder. Todos in this folder will have their folder_id set to null."""
    uid = _require_user_id()
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
    uid = _require_user_id()
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
    """Create a new todo. Priority: 0=none, 1=low, 2=medium, 3=high. Deadline format: ISO 8601."""
    uid = _require_user_id()
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
    uid = _require_user_id()
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
    uid = _require_user_id()
    async with async_session_factory() as session:
        return await svc.delete_todo(session, uid, todo_id)


@mcp.tool()
async def toggle_todo(todo_id: str) -> dict:
    """Toggle a todo's completion status."""
    uid = _require_user_id()
    async with async_session_factory() as session:
        return await svc.toggle_todo(session, uid, todo_id)


@mcp.tool()
async def get_folder_stats(folder_id: str) -> dict:
    """Get completion statistics for a todo folder: total, completed, active, completion_pct."""
    uid = _require_user_id()
    async with async_session_factory() as session:
        return await svc.get_folder_stats(session, uid, folder_id)


if __name__ == "__main__":
    mcp.run()
