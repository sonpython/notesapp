from pydantic import BaseModel
from datetime import datetime


class TelegramStatusResponse(BaseModel):
    is_linked: bool
    is_enabled: bool
    chat_id: str | None = None
    bot_linked_at: datetime | None = None


class TelegramLinkResponse(BaseModel):
    link_code: str
    bot_username: str


class TelegramWebhookPayload(BaseModel):
    """Simplified Telegram webhook update"""
    update_id: int
    message: dict | None = None
