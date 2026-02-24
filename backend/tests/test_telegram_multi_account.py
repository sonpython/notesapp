"""Tests for Telegram multi-account linking.

Verifies that one Telegram chat_id can be linked to multiple NotesApp accounts
and that commands query data across all linked accounts.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.database import get_db
from app.main import app

CHAT_ID = "123456789"
WEBHOOK_URL = "/api/telegram/webhook"


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine):
    """Provide a raw async session for direct DB setup/teardown."""
    factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def webhook_client(test_engine: AsyncEngine):
    """Unauthenticated client for webhook endpoint with mocked Telegram API."""
    factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def two_linked_accounts(db_session: AsyncSession):
    """Create two NotesApp accounts both linked to the same Telegram chat_id.

    Returns (user_id_a, user_id_b) where user_id_a is most recently linked.
    """
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    tg_id_a = str(uuid.uuid4())
    tg_id_b = str(uuid.uuid4())

    # Create user rows so display_name is available for grouped output
    await db_session.execute(
        text("INSERT INTO users (id, display_name) VALUES (:id, :name)"),
        {"id": user_a, "name": "Alice"},
    )
    await db_session.execute(
        text("INSERT INTO users (id, display_name) VALUES (:id, :name)"),
        {"id": user_b, "name": "Bob"},
    )

    # User B linked first (older bot_linked_at)
    await db_session.execute(
        text("""
            INSERT INTO telegram_settings (id, user_id, chat_id, is_enabled, bot_linked_at, backup_enabled, backup_retention, created_at)
            VALUES (:id, :uid, :cid, true, :linked_at, false, 5, now())
        """),
        {"id": tg_id_b, "uid": user_b, "cid": CHAT_ID, "linked_at": datetime(2026, 1, 1, tzinfo=UTC)},
    )
    # User A linked second (newer bot_linked_at)
    await db_session.execute(
        text("""
            INSERT INTO telegram_settings (id, user_id, chat_id, is_enabled, bot_linked_at, backup_enabled, backup_retention, created_at)
            VALUES (:id, :uid, :cid, true, :linked_at, false, 5, now())
        """),
        {"id": tg_id_a, "uid": user_a, "cid": CHAT_ID, "linked_at": datetime(2026, 2, 1, tzinfo=UTC)},
    )
    await db_session.commit()

    yield user_a, user_b

    # Cleanup
    await db_session.execute(text("DELETE FROM todos WHERE user_id IN (:a, :b)"), {"a": user_a, "b": user_b})
    await db_session.execute(text("DELETE FROM notes WHERE user_id IN (:a, :b)"), {"a": user_a, "b": user_b})
    await db_session.execute(text("DELETE FROM telegram_settings WHERE user_id IN (:a, :b)"), {"a": user_a, "b": user_b})
    await db_session.execute(text("DELETE FROM users WHERE id IN (:a, :b)"), {"a": user_a, "b": user_b})
    await db_session.commit()


def _webhook_payload(update_id: int, text_msg: str, chat_id: str = CHAT_ID) -> dict:
    """Build a minimal Telegram webhook payload."""
    return {
        "update_id": update_id,
        "message": {"text": text_msg, "chat": {"id": int(chat_id)}},
    }


@pytest.mark.asyncio
@patch("app.routers.telegram.send_telegram_message", new_callable=AsyncMock, return_value=True)
async def test_start_does_not_clear_existing_link(
    mock_send, webhook_client: AsyncClient, db_session: AsyncSession
):
    """Linking a new account should NOT unlink existing accounts from the same chat_id."""
    user_old = str(uuid.uuid4())
    user_new = str(uuid.uuid4())
    tg_old_id = str(uuid.uuid4())
    tg_new_id = str(uuid.uuid4())

    # Pre-existing linked account
    await db_session.execute(
        text("""
            INSERT INTO telegram_settings (id, user_id, chat_id, is_enabled, bot_linked_at, backup_enabled, backup_retention, created_at)
            VALUES (:id, :uid, :cid, true, now(), false, 5, now())
        """),
        {"id": tg_old_id, "uid": user_old, "cid": CHAT_ID},
    )
    # New account with a link_code pending
    await db_session.execute(
        text("""
            INSERT INTO telegram_settings (id, user_id, link_code, is_enabled, backup_enabled, backup_retention, created_at)
            VALUES (:id, :uid, :code, true, false, 5, now())
        """),
        {"id": tg_new_id, "uid": user_new, "code": "TESTCODE"},
    )
    await db_session.commit()

    # Trigger /start with the new account's code
    resp = await webhook_client.post(
        WEBHOOK_URL, json=_webhook_payload(1, "/start TESTCODE")
    )
    assert resp.status_code == 200

    # Verify old account still has chat_id
    row = await db_session.execute(
        text("SELECT chat_id FROM telegram_settings WHERE user_id = :uid"),
        {"uid": user_old},
    )
    old_chat = row.scalar()
    assert old_chat == CHAT_ID, "Old account should still be linked"

    # Verify new account is also linked
    row2 = await db_session.execute(
        text("SELECT chat_id FROM telegram_settings WHERE user_id = :uid"),
        {"uid": user_new},
    )
    new_chat = row2.scalar()
    assert new_chat == CHAT_ID, "New account should be linked"

    # Cleanup
    await db_session.execute(text("DELETE FROM telegram_settings WHERE user_id IN (:a, :b)"), {"a": user_old, "b": user_new})
    await db_session.commit()


@pytest.mark.asyncio
@patch("app.routers.telegram.send_telegram_message", new_callable=AsyncMock, return_value=True)
async def test_list_shows_todos_from_all_accounts(
    mock_send, webhook_client: AsyncClient, db_session: AsyncSession, two_linked_accounts
):
    """'/list' should show todos from ALL linked NotesApp accounts."""
    user_a, user_b = two_linked_accounts

    # Create todos for each account
    await db_session.execute(
        text("INSERT INTO todos (id, user_id, title, is_completed, priority, sort_order) VALUES (:id, :uid, :t, false, 3, 0)"),
        {"id": str(uuid.uuid4()), "uid": user_a, "t": "Todo from Account A"},
    )
    await db_session.execute(
        text("INSERT INTO todos (id, user_id, title, is_completed, priority, sort_order) VALUES (:id, :uid, :t, false, 2, 0)"),
        {"id": str(uuid.uuid4()), "uid": user_b, "t": "Todo from Account B"},
    )
    await db_session.commit()

    resp = await webhook_client.post(WEBHOOK_URL, json=_webhook_payload(2, "/list"))
    assert resp.status_code == 200

    # Check grouped output contains user names and both todos
    sent_text = mock_send.call_args_list[-1][0][1]
    assert "Alice" in sent_text, "Should show Alice's account name"
    assert "Bob" in sent_text, "Should show Bob's account name"
    assert "Todo from Account A" in sent_text
    assert "Todo from Account B" in sent_text


@pytest.mark.asyncio
@patch("app.routers.telegram.send_telegram_message", new_callable=AsyncMock, return_value=True)
async def test_todo_creates_in_most_recent_account(
    mock_send, webhook_client: AsyncClient, db_session: AsyncSession, two_linked_accounts
):
    """'/todo' should create in the most recently linked account (user_a)."""
    user_a, user_b = two_linked_accounts

    resp = await webhook_client.post(
        WEBHOOK_URL, json=_webhook_payload(3, "/todo Test from Telegram")
    )
    assert resp.status_code == 200

    # Check todo was created for user_a (most recent)
    row = await db_session.execute(
        text("SELECT user_id FROM todos WHERE title = 'Test from Telegram'"),
    )
    owner = str(row.scalar())
    assert owner == user_a, "Todo should be created in the most recently linked account"


@pytest.mark.asyncio
@patch("app.routers.telegram.send_telegram_message", new_callable=AsyncMock, return_value=True)
async def test_search_finds_notes_from_all_accounts(
    mock_send, webhook_client: AsyncClient, db_session: AsyncSession, two_linked_accounts
):
    """'/search' should find notes across all linked accounts."""
    user_a, user_b = two_linked_accounts

    await db_session.execute(
        text("INSERT INTO notes (id, user_id, title, content, is_pinned, is_archived) VALUES (:id, :uid, :t, :c, false, false)"),
        {"id": str(uuid.uuid4()), "uid": user_a, "t": "Recipe Chicken", "c": "some content"},
    )
    await db_session.execute(
        text("INSERT INTO notes (id, user_id, title, content, is_pinned, is_archived) VALUES (:id, :uid, :t, :c, false, false)"),
        {"id": str(uuid.uuid4()), "uid": user_b, "t": "Recipe Beef", "c": "other content"},
    )
    await db_session.commit()

    resp = await webhook_client.post(
        WEBHOOK_URL, json=_webhook_payload(4, '/search "Recipe"')
    )
    assert resp.status_code == 200

    # The search should return results from both accounts
    sent_text = mock_send.call_args_list[-1][0][1]
    assert "2" in sent_text, "Should find 2 notes across both accounts"


@pytest.mark.asyncio
@patch("app.routers.telegram.send_telegram_message", new_callable=AsyncMock, return_value=True)
async def test_done_works_across_accounts(
    mock_send, webhook_client: AsyncClient, db_session: AsyncSession, two_linked_accounts
):
    """'/done' should be able to complete a todo from any linked account."""
    user_a, user_b = two_linked_accounts

    # Create a high-priority todo in user_b (will be #1 in list)
    todo_id = str(uuid.uuid4())
    await db_session.execute(
        text("INSERT INTO todos (id, user_id, title, is_completed, priority, sort_order) VALUES (:id, :uid, :t, false, 3, 0)"),
        {"id": todo_id, "uid": user_b, "t": "Cross-account todo"},
    )
    await db_session.commit()

    resp = await webhook_client.post(WEBHOOK_URL, json=_webhook_payload(5, "/done 1"))
    assert resp.status_code == 200

    # Verify todo is completed
    row = await db_session.execute(
        text("SELECT is_completed FROM todos WHERE id = :id"), {"id": todo_id}
    )
    assert row.scalar() is True


@pytest.mark.asyncio
@patch("app.routers.telegram.send_telegram_message", new_callable=AsyncMock, return_value=True)
async def test_unlinked_chat_gets_warning(mock_send, webhook_client: AsyncClient):
    """Commands from unlinked chat_id should get a warning message."""
    resp = await webhook_client.post(
        WEBHOOK_URL,
        json={
            "update_id": 99,
            "message": {"text": "/list", "chat": {"id": 999999999}},
        },
    )
    assert resp.status_code == 200
    sent_text = mock_send.call_args[0][1]
    assert "link your account" in sent_text.lower()
