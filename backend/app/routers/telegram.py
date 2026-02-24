"""Telegram router -- link/unlink and webhook endpoints."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.note import Note
from app.models.telegram import TelegramSettings
from app.models.todo import Todo
from app.models.user import User
from app.rate_limiter import WEBHOOK_RATE_LIMIT, limiter
from app.schemas.telegram import (
    TelegramLinkResponse,
    TelegramStatusResponse,
    TelegramWebhookPayload,
)
from app.services.telegram_service import answer_callback_query, send_telegram_message

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
        await send_telegram_message(
            record.chat_id,
            "🔓 Tài khoản đã được hủy liên kết.\n\nBạn sẽ không nhận được thông báo nữa.",
        )

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

    # Get all user_ids linked to this chat_id (multi-account)
    user_ids = await _get_user_ids(session, chat_id)
    if not user_ids:
        await send_telegram_message(
            chat_id, "⚠️ Please link your account first via the app settings."
        )
        return {"ok": True}

    # /todo <title> - Create todo (uses most recently linked account)
    if text.startswith("/todo "):
        title = text[6:].strip()
        if title:
            await _handle_todo(session, chat_id, user_ids[0], title)
        else:
            await send_telegram_message(chat_id, "Usage: `/todo Buy groceries`")
        return {"ok": True}

    # /list - List active todos (from all linked accounts)
    if text == "/list":
        await _handle_list(session, chat_id, user_ids)
        return {"ok": True}

    # /done <number> - Mark complete
    if text.startswith("/done "):
        num = text[6:].strip()
        if num.isdigit():
            await _handle_done(session, chat_id, user_ids, int(num))
        else:
            await send_telegram_message(chat_id, "Usage: `/done 1`")
        return {"ok": True}

    # /search <query> - Search notes (across all linked accounts)
    if text.startswith("/search "):
        query = text[8:].strip()
        if query:
            await _handle_search(session, chat_id, user_ids, query)
        else:
            await send_telegram_message(chat_id, "Usage: `/search keyword`")
        return {"ok": True}

    return {"ok": True}


async def _get_user_ids(session: AsyncSession, chat_id: str) -> list[str]:
    """Get all user_ids linked to a chat_id (multi-account support)."""
    stmt = (
        select(TelegramSettings.user_id)
        .where(TelegramSettings.chat_id == chat_id)
        .order_by(TelegramSettings.bot_linked_at.desc())
    )
    result = await session.execute(stmt)
    return [str(row) for row in result.scalars().all()]


async def _get_user_names(session: AsyncSession, user_ids: list[str]) -> dict[str, str]:
    """Get display_name for each user_id. Returns {user_id: display_name}."""
    if len(user_ids) <= 1:
        return {}
    stmt = select(User.id, User.display_name).where(User.id.in_(user_ids))
    result = await session.execute(stmt)
    return {str(uid): name for uid, name in result.all()}


async def _handle_start(session: AsyncSession, chat_id: str, code: str) -> None:
    """Link account via code."""
    stmt = select(TelegramSettings).where(TelegramSettings.link_code == code)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        record.chat_id = chat_id
        record.link_code = None
        record.bot_linked_at = datetime.now(UTC)
        await session.commit()
        await send_telegram_message(
            chat_id,
            "✅ Liên kết thành công!\n\nCommands:\n/search <query> - Tìm kiếm note\n/todo <title> - Tạo todo\n/list - Xem danh sách todo\n/done <n> - Hoàn thành todo",
        )
    else:
        await send_telegram_message(
            chat_id,
            "❌ Mã không hợp lệ hoặc đã hết hạn.\n\nVui lòng tạo mã mới trong Settings → Telegram.",
        )


async def _handle_todo(session: AsyncSession, chat_id: str, user_id: str, title: str) -> None:
    """Create a new todo."""
    todo = Todo(user_id=user_id, title=title)
    session.add(todo)
    await session.commit()
    await send_telegram_message(chat_id, f"✅ Created: *{title}*")


async def _handle_list(session: AsyncSession, chat_id: str, user_ids: list[str]) -> None:
    """List active todos from all linked accounts, grouped by user."""
    stmt = (
        select(Todo)
        .where(
            Todo.user_id.in_(user_ids),
            Todo.is_completed == False,  # noqa: E712
            Todo.parent_id == None,  # noqa: E711
        )
        .order_by(Todo.priority.desc(), Todo.created_at.desc())
        .limit(10)
    )
    result = await session.execute(stmt)
    todos = list(result.scalars().all())

    if not todos:
        await send_telegram_message(chat_id, "📝 No active todos. Create one with `/todo Buy milk`")
        return

    names = await _get_user_names(session, user_ids)
    multi = len(names) > 1

    lines = ["📝 *Active Todos:*"]
    counter = 1
    if multi:
        # Group by user
        from collections import defaultdict

        by_user: dict[str, list[Todo]] = defaultdict(list)
        for t in todos:
            by_user[str(t.user_id)].append(t)
        for uid in user_ids:
            user_todos = by_user.get(uid, [])
            if not user_todos:
                continue
            lines.append(f"\n👤 *{names.get(uid, 'Unknown')}:*")
            for t in user_todos:
                pri = ["", "🔵", "🟡", "🔴"][t.priority] if t.priority else ""
                lines.append(f"{counter}. {pri}{t.title}")
                counter += 1
    else:
        for t in todos:
            pri = ["", "🔵", "🟡", "🔴"][t.priority] if t.priority else ""
            lines.append(f"{counter}. {pri}{t.title}")
            counter += 1
    lines.append("\n_Use /done <n> to complete_")
    await send_telegram_message(chat_id, "\n".join(lines))


async def _handle_done(session: AsyncSession, chat_id: str, user_ids: list[str], num: int) -> None:
    """Mark todo complete by list number (across all linked accounts)."""
    stmt = (
        select(Todo)
        .where(
            Todo.user_id.in_(user_ids),
            Todo.is_completed == False,  # noqa: E712
            Todo.parent_id == None,  # noqa: E711
        )
        .order_by(Todo.priority.desc(), Todo.created_at.desc())
        .limit(10)
    )
    result = await session.execute(stmt)
    todos = list(result.scalars().all())

    if num < 1 or num > len(todos):
        await send_telegram_message(chat_id, f"⚠️ Invalid number. Use 1-{len(todos)}")
        return

    todo = todos[num - 1]
    title = todo.title

    todo.is_completed = True
    todo.completed_at = datetime.now(UTC)
    await session.commit()
    await send_telegram_message(chat_id, f"✅ Completed: *{title}*")


async def _handle_search(
    session: AsyncSession, chat_id: str, user_ids: list[str], query: str
) -> None:
    """Search notes across all linked accounts with Vietnamese diacritics support."""
    search_pattern = f"%{query}%"

    # Check for exact match (query in double quotes)
    if query.startswith('"') and query.endswith('"') and len(query) > 2:
        exact_term = query[1:-1]
        stmt = (
            select(Note)
            .where(
                Note.user_id.in_(user_ids),
                Note.is_archived == False,  # noqa: E712
                or_(
                    Note.title.contains(exact_term),
                    Note.content.contains(exact_term),
                ),
            )
            .order_by(Note.updated_at.desc())
            .limit(10)
        )
    else:
        # Fuzzy match with unaccent for Vietnamese diacritics
        stmt = (
            select(Note)
            .where(
                Note.user_id.in_(user_ids),
                Note.is_archived == False,  # noqa: E712
                or_(
                    func.unaccent(func.lower(Note.title)).ilike(
                        func.unaccent(func.lower(search_pattern))
                    ),
                    func.unaccent(func.lower(Note.content)).ilike(
                        func.unaccent(func.lower(search_pattern))
                    ),
                ),
            )
            .order_by(Note.updated_at.desc())
            .limit(10)
        )
    result = await session.execute(stmt)
    notes = list(result.scalars().all())

    if not notes:
        await send_telegram_message(chat_id, f"🔍 Không tìm thấy note nào với từ khóa: *{query}*")
        return

    names = await _get_user_names(session, user_ids)
    multi = len(names) > 1

    # Build inline keyboard with note titles, grouped by user if multi-account
    keyboard = []
    if multi:
        from collections import defaultdict

        by_user: dict[str, list] = defaultdict(list)
        for note in notes:
            by_user[str(note.user_id)].append(note)
        for uid in user_ids:
            user_notes = by_user.get(uid, [])
            if not user_notes:
                continue
            # Section header as a non-clickable button
            keyboard.append([{"text": f"👤 {names.get(uid, 'Unknown')}", "callback_data": "noop"}])
            for note in user_notes:
                title = note.title or "Untitled"
                if len(title) > 35:
                    title = title[:32] + "..."
                keyboard.append([{"text": f"📝 {title}", "callback_data": f"view_note:{note.id}"}])
    else:
        for note in notes:
            title = note.title or "Untitled"
            if len(title) > 40:
                title = title[:37] + "..."
            keyboard.append([{"text": f"📝 {title}", "callback_data": f"view_note:{note.id}"}])

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

    # Get all user_ids linked to this chat_id
    user_ids = await _get_user_ids(session, chat_id)
    if not user_ids:
        await send_telegram_message(chat_id, "⚠️ Vui lòng liên kết tài khoản trước.")
        return

    # Handle view_note callback
    if data.startswith("view_note:"):
        note_id = data[10:]  # Remove "view_note:" prefix
        await _handle_view_note(session, chat_id, user_ids, note_id)


def _html_to_text(html: str) -> str:
    """Convert HTML content to plain text with Telegram markdown."""
    import re

    text = html
    # Convert common HTML elements to text/markdown equivalents
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(
        r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n*\1*\n", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<b[^>]*>(.*?)</b>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"_\1_", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<i[^>]*>(.*?)</i>", r"_\1_", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"• \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"\2 (\1)", text, flags=re.IGNORECASE | re.DOTALL
    )
    # Remove remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +", " ", text)
    return text.strip()


async def _handle_view_note(
    session: AsyncSession, chat_id: str, user_ids: list[str], note_id: str
) -> None:
    """Display note content from any linked account."""
    stmt = select(Note).where(Note.id == note_id, Note.user_id.in_(user_ids))
    result = await session.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        await send_telegram_message(chat_id, "⚠️ Note không tồn tại hoặc bạn không có quyền xem.")
        return

    title = note.title or "Untitled"
    content = _html_to_text(note.content) if note.content else "(Không có nội dung)"

    # Truncate very long content for Telegram (4096 char limit)
    if len(content) > 3500:
        content = content[:3500] + "\n\n_...nội dung bị cắt ngắn..._"

    # Format message
    message = f"📝 *{title}*\n\n{content}"
    await send_telegram_message(chat_id, message)
