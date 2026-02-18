"""Telegram router -- link/unlink and webhook endpoints."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.note import Note
from app.models.telegram import TelegramSettings
from app.models.todo import Todo
from app.schemas.telegram import (
    TelegramLinkResponse,
    TelegramStatusResponse,
    TelegramWebhookPayload,
)
from app.services.telegram_service import send_telegram_message, answer_callback_query
from app.rate_limiter import limiter, WEBHOOK_RATE_LIMIT

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

    # Notify user via Telegram before unlinking
    if record.chat_id:
        await send_telegram_message(record.chat_id, "🔓 Tài khoản đã được hủy liên kết.\n\nBạn sẽ không nhận được thông báo nữa.")

    record.chat_id = None
    record.link_code = None
    record.bot_linked_at = None

    await session.commit()
    return {"status": "unlinked"}


@router.post("/webhook", status_code=200)
@limiter.limit(WEBHOOK_RATE_LIMIT)
async def telegram_webhook(
    request: Request,
    payload: TelegramWebhookPayload,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Public endpoint (no auth). Handle incoming Telegram updates.

    Commands:
    - /start <code> - Link account
    - /todo <title> - Create a new todo
    - /list - List active todos
    - /done <number> - Mark todo complete (by list number)
    - /search <query> - Search notes by title/content
    """
    # Handle callback queries (inline keyboard button clicks)
    if payload.callback_query:
        await _handle_callback_query(session, payload.callback_query)
        return {"ok": True}

    message = payload.message
    if message is None:
        return {"ok": True}

    text: str = message.get("text", "").strip()
    chat_id: str | None = str(message.get("chat", {}).get("id"))

    if not text or chat_id is None:
        return {"ok": True}

    # /start <code> - Link account
    if text.startswith("/start "):
        code = text[7:].strip()
        if code:
            await _handle_start(session, chat_id, code)
        return {"ok": True}

    # Get user_id from chat_id for other commands
    user_id = await _get_user_id(session, chat_id)
    if user_id is None:
        await send_telegram_message(chat_id, "⚠️ Please link your account first via the app settings.")
        return {"ok": True}

    # /todo <title> - Create todo
    if text.startswith("/todo "):
        title = text[6:].strip()
        if title:
            await _handle_todo(session, chat_id, user_id, title)
        else:
            await send_telegram_message(chat_id, "Usage: `/todo Buy groceries`")
        return {"ok": True}

    # /list - List active todos
    if text == "/list":
        await _handle_list(session, chat_id, user_id)
        return {"ok": True}

    # /done <number> - Mark complete
    if text.startswith("/done "):
        num = text[6:].strip()
        if num.isdigit():
            await _handle_done(session, chat_id, user_id, int(num))
        else:
            await send_telegram_message(chat_id, "Usage: `/done 1`")
        return {"ok": True}

    # /search <query> - Search notes
    if text.startswith("/search "):
        query = text[8:].strip()
        if query:
            await _handle_search(session, chat_id, user_id, query)
        else:
            await send_telegram_message(chat_id, "Usage: `/search keyword`")
        return {"ok": True}

    return {"ok": True}


async def _get_user_id(session: AsyncSession, chat_id: str) -> str | None:
    """Get user_id from chat_id."""
    stmt = select(TelegramSettings.user_id).where(TelegramSettings.chat_id == chat_id)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    return str(row) if row else None


async def _handle_start(session: AsyncSession, chat_id: str, code: str) -> None:
    """Link account via code."""
    stmt = select(TelegramSettings).where(TelegramSettings.link_code == code)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        record.chat_id = chat_id
        record.link_code = None
        record.bot_linked_at = datetime.now(timezone.utc)
        await session.commit()
        await send_telegram_message(chat_id, "✅ Liên kết thành công!\n\nCommands:\n/search <query> - Tìm kiếm note\n/todo <title> - Tạo todo\n/list - Xem danh sách todo\n/done <n> - Hoàn thành todo")
    else:
        await send_telegram_message(chat_id, "❌ Mã không hợp lệ hoặc đã hết hạn.\n\nVui lòng tạo mã mới trong Settings → Telegram.")


async def _handle_todo(session: AsyncSession, chat_id: str, user_id: str, title: str) -> None:
    """Create a new todo."""
    todo = Todo(user_id=user_id, title=title)
    session.add(todo)
    await session.commit()
    await send_telegram_message(chat_id, f"✅ Created: *{title}*")


async def _handle_list(session: AsyncSession, chat_id: str, user_id: str) -> None:
    """List active todos."""
    stmt = select(Todo).where(
        Todo.user_id == user_id,
        Todo.is_completed == False,  # noqa: E712
        Todo.parent_id == None,  # noqa: E711
    ).order_by(Todo.priority.desc(), Todo.created_at.desc()).limit(10)
    result = await session.execute(stmt)
    todos = list(result.scalars().all())

    if not todos:
        await send_telegram_message(chat_id, "📝 No active todos. Create one with `/todo Buy milk`")
        return

    lines = ["📝 *Active Todos:*"]
    for i, t in enumerate(todos, 1):
        pri = ["", "🔵", "🟡", "🔴"][t.priority] if t.priority else ""
        lines.append(f"{i}. {pri}{t.title}")
    lines.append("\n_Use /done <n> to complete_")
    await send_telegram_message(chat_id, "\n".join(lines))


async def _handle_done(session: AsyncSession, chat_id: str, user_id: str, num: int) -> None:
    """Mark todo complete by list number."""
    stmt = select(Todo).where(
        Todo.user_id == user_id,
        Todo.is_completed == False,  # noqa: E712
        Todo.parent_id == None,  # noqa: E711
    ).order_by(Todo.priority.desc(), Todo.created_at.desc()).limit(10)
    result = await session.execute(stmt)
    todos = list(result.scalars().all())

    if num < 1 or num > len(todos):
        await send_telegram_message(chat_id, f"⚠️ Invalid number. Use 1-{len(todos)}")
        return

    todo = todos[num - 1]
    title = todo.title

    todo.is_completed = True
    todo.completed_at = datetime.now(timezone.utc)
    await session.commit()
    await send_telegram_message(chat_id, f"✅ Completed: *{title}*")


async def _handle_search(session: AsyncSession, chat_id: str, user_id: str, query: str) -> None:
    """Search notes by title or content."""
    search_pattern = f"%{query}%"
    stmt = select(Note).where(
        Note.user_id == user_id,
        Note.is_archived == False,  # noqa: E712
        or_(
            Note.title.ilike(search_pattern),
            Note.content.ilike(search_pattern),
        ),
    ).order_by(Note.updated_at.desc()).limit(10)
    result = await session.execute(stmt)
    notes = list(result.scalars().all())

    if not notes:
        await send_telegram_message(chat_id, f"🔍 Không tìm thấy note nào với từ khóa: *{query}*")
        return

    # Build inline keyboard with note titles
    keyboard = []
    for note in notes:
        title = note.title or "Untitled"
        # Truncate long titles
        if len(title) > 40:
            title = title[:37] + "..."
        keyboard.append([{
            "text": f"📝 {title}",
            "callback_data": f"view_note:{note.id}",
        }])

    reply_markup = {"inline_keyboard": keyboard}
    await send_telegram_message(
        chat_id,
        f"🔍 Tìm thấy {len(notes)} note với từ khóa: *{query}*\n\nChọn note để xem nội dung:",
        reply_markup=reply_markup,
    )


async def _handle_callback_query(session: AsyncSession, callback_query: dict) -> None:
    """Handle inline keyboard button clicks."""
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id"))

    if not chat_id:
        return

    # Acknowledge the callback
    await answer_callback_query(callback_id)

    # Get user_id from chat_id
    user_id = await _get_user_id(session, chat_id)
    if user_id is None:
        await send_telegram_message(chat_id, "⚠️ Vui lòng liên kết tài khoản trước.")
        return

    # Handle view_note callback
    if data.startswith("view_note:"):
        note_id = data[10:]  # Remove "view_note:" prefix
        await _handle_view_note(session, chat_id, user_id, note_id)


async def _handle_view_note(session: AsyncSession, chat_id: str, user_id: str, note_id: str) -> None:
    """Display note content."""
    stmt = select(Note).where(Note.id == note_id, Note.user_id == user_id)
    result = await session.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        await send_telegram_message(chat_id, "⚠️ Note không tồn tại hoặc bạn không có quyền xem.")
        return

    title = note.title or "Untitled"
    content = note.content or "(Không có nội dung)"

    # Truncate very long content for Telegram (4096 char limit)
    if len(content) > 3500:
        content = content[:3500] + "\n\n_...nội dung bị cắt ngắn..._"

    # Format message
    message = f"📝 *{title}*\n\n{content}"
    await send_telegram_message(chat_id, message)
