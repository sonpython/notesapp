"""Telegram router -- link/unlink and webhook endpoints."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.telegram import TelegramSettings
from app.schemas.telegram import (
    TelegramLinkResponse,
    TelegramStatusResponse,
    TelegramWebhookPayload,
)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

# Derive the bot username from the token (or fallback placeholder)
_BOT_USERNAME = "NotesAppBot"


@router.get("/status", response_model=TelegramStatusResponse)
async def get_telegram_status(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TelegramStatusResponse:
    """Get the Telegram link status for the current user."""
    stmt = select(TelegramSettings).where(TelegramSettings.user_id == user_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        return TelegramStatusResponse(
            is_linked=False,
            is_enabled=False,
        )

    return TelegramStatusResponse(
        is_linked=record.chat_id is not None,
        is_enabled=record.is_enabled,
        chat_id=record.chat_id,
        bot_linked_at=record.bot_linked_at,
    )


@router.post("/link", response_model=TelegramLinkResponse)
async def link_telegram(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TelegramLinkResponse:
    """Generate a random 8-char link code; upsert telegram_settings row."""
    link_code = secrets.token_urlsafe(6)[:8]

    stmt = select(TelegramSettings).where(TelegramSettings.user_id == user_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        record = TelegramSettings(
            user_id=user_id,
            link_code=link_code,
        )
        session.add(record)
    else:
        record.link_code = link_code

    await session.commit()
    await session.refresh(record)

    return TelegramLinkResponse(
        link_code=link_code,
        bot_username=_BOT_USERNAME,
    )


@router.post("/unlink", status_code=200)
async def unlink_telegram(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Remove chat_id and clear the link code for the current user."""
    stmt = select(TelegramSettings).where(TelegramSettings.user_id == user_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=404, detail="Telegram settings not found")

    record.chat_id = None
    record.link_code = None
    record.bot_linked_at = None

    await session.commit()
    return {"status": "unlinked"}


@router.post("/webhook", status_code=200)
async def telegram_webhook(
    payload: TelegramWebhookPayload,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Public endpoint (no auth). Handle incoming Telegram updates.

    If the message text starts with ``/start ``, extract the link code,
    find the matching telegram_settings row, and save the chat_id.
    """
    message = payload.message
    if message is None:
        return {"ok": True}

    text: str = message.get("text", "")
    chat_id: str | None = str(message.get("chat", {}).get("id"))

    if not text.startswith("/start ") or chat_id is None:
        return {"ok": True}

    code = text[len("/start "):].strip()
    if not code:
        return {"ok": True}

    stmt = select(TelegramSettings).where(TelegramSettings.link_code == code)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        return {"ok": True, "detail": "Unknown link code"}

    record.chat_id = chat_id
    record.link_code = None
    record.bot_linked_at = datetime.now(timezone.utc)
    await session.commit()

    return {"ok": True, "detail": "Linked successfully"}
