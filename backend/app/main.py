"""FastAPI application entry point for the NotesApp backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.tasks.reminders import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: start scheduler on startup, stop on shutdown."""
    start_scheduler()
    logger.info("Application startup complete")
    yield
    stop_scheduler()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="NotesApp API",
    version="0.1.0",
    lifespan=lifespan,
)

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
    from app.routers import auth, folders, notes, telegram, todos

    app.include_router(auth.router)
    app.include_router(notes.router)
    app.include_router(folders.router)
    app.include_router(todos.router)
    app.include_router(telegram.router)


_register_routers()
