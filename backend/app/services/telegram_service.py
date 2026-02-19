# Send Telegram messages and files via Bot API using httpx
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Max file size Telegram allows for bot uploads (50 MB)
TELEGRAM_MAX_UPLOAD_BYTES = 50 * 1024 * 1024


async def send_telegram_message(
    chat_id: str,
    text: str,
    reply_markup: dict | None = None,
) -> bool:
    """Send a message to a Telegram chat. Returns True on success."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.status_code == 200


async def answer_callback_query(callback_query_id: str, text: str | None = None) -> bool:
    """Answer a callback query to remove the loading indicator."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload: dict = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.status_code == 200


async def get_bot_username() -> str:
    """Get the bot's username from Telegram API."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return "notesapp_bot"
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("result", {}).get("username", "notesapp_bot")
    return "notesapp_bot"


async def send_document(
    chat_id: str,
    file_bytes: bytes,
    filename: str,
    caption: str | None = None,
) -> tuple[str, int] | None:
    """Upload a document to a Telegram chat.

    Returns (file_id, message_id) on success, or None on failure.
    Raises ValueError if file exceeds Telegram's 50 MB upload limit.
    """
    if len(file_bytes) > TELEGRAM_MAX_UPLOAD_BYTES:
        raise ValueError(f"File size {len(file_bytes)} bytes exceeds Telegram 50 MB limit")

    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("send_document: TELEGRAM_BOT_TOKEN not configured")
        return None

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    files = {"document": (filename, file_bytes, "application/octet-stream")}
    data: dict[str, str] = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, files=files, data=data)
            if response.status_code != 200:
                logger.error("send_document: Telegram API error %s", response.text)
                return None
            result = response.json().get("result", {})
            file_id = result.get("document", {}).get("file_id")
            message_id = result.get("message_id")
            if not file_id or message_id is None:
                logger.error("send_document: unexpected response %s", result)
                return None
            return (file_id, message_id)
    except httpx.TimeoutException:
        logger.error("send_document: request timed out uploading %s", filename)
        return None


async def download_file(file_id: str) -> bytes | None:
    """Download a file from Telegram by its persistent file_id.

    Two-step process: getFile to obtain file_path, then fetch file bytes.
    Returns raw bytes on success, or None on failure.
    Note: Telegram's getFile endpoint supports files up to 20 MB.
    """
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("download_file: TELEGRAM_BOT_TOKEN not configured")
        return None

    token = settings.TELEGRAM_BOT_TOKEN

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: resolve file_id -> file_path
            get_file_url = f"https://api.telegram.org/bot{token}/getFile"
            resp = await client.post(get_file_url, json={"file_id": file_id})
            if resp.status_code != 200:
                logger.error("download_file: getFile error %s", resp.text)
                return None
            file_path = resp.json().get("result", {}).get("file_path")
            if not file_path:
                logger.error("download_file: no file_path in getFile response")
                return None

            # Step 2: download the actual bytes
            download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
            dl_resp = await client.get(download_url)
            if dl_resp.status_code != 200:
                logger.error("download_file: download error %s", dl_resp.status_code)
                return None
            return dl_resp.content
    except httpx.TimeoutException:
        logger.error("download_file: request timed out for file_id %s", file_id)
        return None


async def delete_message(chat_id: str, message_id: int) -> bool:
    """Delete a message from a Telegram chat.

    Used to prune old backup messages when retention limit is exceeded.
    Returns True on success, False on failure (e.g. message already deleted).
    """
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("delete_message: TELEGRAM_BOT_TOKEN not configured")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={"chat_id": chat_id, "message_id": message_id})
            if response.status_code != 200:
                logger.warning(
                    "delete_message: Telegram API returned %s: %s",
                    response.status_code,
                    response.text,
                )
                return False
            return True
    except httpx.TimeoutException:
        logger.error("delete_message: request timed out for message_id %s", message_id)
        return False
