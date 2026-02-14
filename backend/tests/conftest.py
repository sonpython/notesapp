"""Pytest fixtures for NotesApp backend tests.

Uses PostgreSQL with proper async session management.
"""

from __future__ import annotations

import os
import uuid as uuid_module
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.main import app


def _get_test_db_url() -> str:
    """Get test database URL, ensuring asyncpg driver."""
    url = os.environ.get("TEST_DATABASE_URL", settings.DATABASE_URL)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh engine for each test."""
    engine = create_async_engine(
        _get_test_db_url(),
        echo=False,
        pool_size=5,
        max_overflow=0,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
def test_user_id() -> str:
    """Return a test user UUID string."""
    return str(uuid_module.uuid4())


@pytest_asyncio.fixture(scope="function")
async def auth_client(
    test_engine: AsyncEngine,
    test_user_id: str,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with mocked auth and isolated session."""

    # Track created resources for cleanup
    created_note_ids: list[str] = []

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    async def override_get_current_user() -> str:
        return test_user_id

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Wrap post to track created notes for cleanup
        original_post = client.post

        async def tracked_post(url: str, **kwargs):
            response = await original_post(url, **kwargs)
            if url.startswith("/api/notes") and response.status_code == 201:
                data = response.json()
                if "id" in data:
                    created_note_ids.append(data["id"])
            return response

        client.post = tracked_post
        yield client

    # Cleanup: delete created notes
    async with TestSessionLocal() as session:
        from sqlalchemy import text
        for note_id in created_note_ids:
            await session.execute(
                text("DELETE FROM notes WHERE id = :id"),
                {"id": note_id}
            )
        await session.commit()

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(test_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """Create unauthenticated test client."""

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
