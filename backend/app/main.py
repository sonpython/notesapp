"""FastAPI application entry point for the NotesApp backend."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.rate_limiter import limiter
from app.services.minio_storage_service import minio_service
from app.tasks.reminders import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: start scheduler on startup, stop on shutdown."""
    start_scheduler()
    # Initialize MinIO bucket
    try:
        await minio_service.ensure_bucket()
    except Exception as e:
        logger.warning(f"MinIO initialization failed (may be unavailable): {e}")

    # Start MCP server lifespan (required for SSE transport)
    mcp_app = app.state.mcp_app
    async with mcp_app.router.lifespan_context(mcp_app):
        logger.info("Application startup complete (MCP SSE ready)")
        yield

    stop_scheduler()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="NotesApp API",
    version="0.1.0",
    description="""
NotesApp API provides endpoints for managing notes, todos, folders, and Telegram integration.

## Features
- **Notes**: Create, read, update, delete notes with markdown support
- **Todos**: Task management with priorities, due dates, and reminders
- **Folders**: Organize notes in nested folder structure
- **Telegram**: Bot integration for creating todos via chat

## Authentication
All endpoints (except health and telegram webhook) require authentication via:
- Session cookie (set by passkey login/register)
- Or Authorization header: `Bearer <token>`
""",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "notes", "description": "Note CRUD operations"},
        {"name": "folders", "description": "Folder management"},
        {"name": "todos", "description": "Todo/task management"},
        {"name": "tags", "description": "Tag management"},
        {"name": "telegram", "description": "Telegram bot integration"},
        {"name": "images", "description": "Image upload and management"},
    ],
)

# --- Rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health check ---
@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a simple health status for monitoring."""
    return {"status": "ok"}


# --- Router registration ---
# Routers are imported inside a helper to keep the top of this file clean
# and to avoid circular-import issues during startup.


def _register_routers() -> None:
    """Import and include all API routers."""
    from app.routers import (
        api_keys,
        auth,
        auth_login,
        auth_register,
        backup,
        folders,
        images,
        notes,
        public_config,
        shared_notes,
        shared_todo_folders_owner,
        shared_todo_folders_public,
        tags,
        telegram,
        todo_folders,
        todos,
    )

    app.include_router(public_config.router)
    app.include_router(shared_notes.router)
    app.include_router(shared_todo_folders_owner.router)
    app.include_router(shared_todo_folders_public.router)
    app.include_router(auth.router)
    app.include_router(auth_register.router)
    app.include_router(auth_login.router)
    app.include_router(notes.router)
    app.include_router(folders.router)
    app.include_router(todo_folders.router)
    app.include_router(todos.router)
    app.include_router(api_keys.router)
    app.include_router(tags.router)
    app.include_router(telegram.router)
    app.include_router(backup.router)
    app.include_router(images.router)


_register_routers()

# --- MCP Server (Streamable HTTP at /api/mcp) ---
from app.middleware.mcp_auth_middleware import McpAuthMiddleware  # noqa: E402

app.add_middleware(McpAuthMiddleware)

from mcp_server import get_mcp_http_app  # noqa: E402

# Create MCP app once and store for lifespan + mount
_mcp_http_app = get_mcp_http_app()
app.state.mcp_app = _mcp_http_app
app.mount("/api/mcp", _mcp_http_app)
