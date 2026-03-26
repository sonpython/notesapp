"""MCP server for NotesApp Todos — exposes todo/folder CRUD as MCP tools.

Supports two transport modes:
1. HTTP (production): Mounted at /mcp in the FastAPI app, auth via API key header
2. Stdio (local dev): Run directly as subprocess with NOTESAPP_API_KEY env var

Claude Desktop config (remote via HTTP):
  {
    "mcpServers": {
      "notesapp-todos": {
        "url": "https://your-domain.com/mcp",
        "headers": {
          "Authorization": "Bearer na_xxxxxxxx..."
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


async def resolve_user_id_from_key(api_key: str) -> str:
    """Validate API key and return the associated user_id."""
    if not api_key:
        raise ValueError("API key is required.")

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    from sqlalchemy import select

    async with async_session_factory() as session:
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await session.execute(stmt)
        api_key_row = result.scalar_one_or_none()

        if api_key_row is None:
            raise ValueError("Invalid API key.")

        if api_key_row.expires_at and api_key_row.expires_at < datetime.now(UTC):
            raise ValueError("API key has expired.")

        api_key_row.last_used_at = datetime.now(UTC)
        await session.commit()

        return str(api_key_row.user_id)


# Stdio mode: resolve user_id from env var once
_stdio_user_id: str | None = None


async def _get_user_id() -> str:
    """Get user_id — from middleware request state, HTTP header, or env var (stdio)."""
    # HTTP mode: read user_id already resolved by McpAuthMiddleware
    try:
        from fastmcp.server.dependencies import get_http_request

        request = get_http_request()
        # Middleware already validated API key and stored user_id
        uid = getattr(request.state, "mcp_user_id", None)
        if uid:
            return uid
    except Exception:
        pass  # Not in HTTP context, fall through to stdio mode

    # Stdio mode: resolve from env var
    global _stdio_user_id
    if _stdio_user_id:
        return _stdio_user_id

    env_key = os.environ.get("NOTESAPP_API_KEY", "")
    if env_key:
        _stdio_user_id = await resolve_user_id_from_key(env_key)
        return _stdio_user_id

    raise ValueError(
        "No authentication. Set NOTESAPP_API_KEY env var "
        "or connect via HTTP with Authorization header."
    )


# -- Folder tools --


@mcp.tool()
async def list_todo_folders() -> list[dict]:
    """List all todo folders for the current user."""
    uid = await _get_user_id()
    async with async_session_factory() as session:
        return await svc.list_folders(session, uid)


@mcp.tool()
async def create_todo_folder(name: str, parent_id: str | None = None) -> dict:
    """Create a new todo folder. Use parent_id to nest under another folder."""
    uid = await _get_user_id()
    async with async_session_factory() as session:
        return await svc.create_folder(session, uid, name, parent_id)


@mcp.tool()
async def update_todo_folder(
    folder_id: str, name: str | None = None, parent_id: str | None = None
) -> dict:
    """Update a todo folder's name or parent."""
    uid = await _get_user_id()
    async with async_session_factory() as session:
        return await svc.update_folder(session, uid, folder_id, name=name, parent_id=parent_id)


@mcp.tool()
async def delete_todo_folder(folder_id: str) -> bool:
    """Delete a todo folder. Todos in this folder will have their folder_id set to null."""
    uid = await _get_user_id()
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
    uid = await _get_user_id()
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
    uid = await _get_user_id()
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
    uid = await _get_user_id()
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
    uid = await _get_user_id()
    async with async_session_factory() as session:
        return await svc.delete_todo(session, uid, todo_id)


@mcp.tool()
async def toggle_todo(todo_id: str) -> dict:
    """Toggle a todo's completion status."""
    uid = await _get_user_id()
    async with async_session_factory() as session:
        return await svc.toggle_todo(session, uid, todo_id)


@mcp.tool()
async def get_folder_stats(folder_id: str) -> dict:
    """Get completion statistics for a todo folder."""
    uid = await _get_user_id()
    async with async_session_factory() as session:
        return await svc.get_folder_stats(session, uid, folder_id)


def get_mcp_http_app():
    """Create the MCP HTTP ASGI app for mounting in FastAPI (streamable-http)."""
    return mcp.http_app(path="/", transport="streamable-http", stateless_http=True)


if __name__ == "__main__":
    mcp.run()
