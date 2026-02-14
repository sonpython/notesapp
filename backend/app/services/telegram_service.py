# Send Telegram messages via Bot API using httpx
import httpx
from app.config import get_settings


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """Send a message to a Telegram chat. Returns True on success."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )
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
