"""SQLAlchemy ORM models for the NotesApp backend.

Import all models here so that ``Base.metadata`` is fully populated when
Alembic or application startup inspects it.
"""

from app.database import Base
from app.models.api_key import ApiKey
from app.models.folder import Folder
from app.models.note import Note
from app.models.passkey_credential import PasskeyCredential
from app.models.tag import NoteTag, Tag, TodoTag
from app.models.telegram import TelegramSettings
from app.models.telegram_backup import TelegramBackup
from app.models.todo import Todo
from app.models.todo_folder import TodoFolder
from app.models.user import User
from app.models.webauthn_challenge import WebAuthnChallenge

__all__ = [
    "ApiKey",
    "Base",
    "Folder",
    "Note",
    "NoteTag",
    "PasskeyCredential",
    "Tag",
    "Todo",
    "TodoFolder",
    "TodoTag",
    "TelegramBackup",
    "TelegramSettings",
    "User",
    "WebAuthnChallenge",
]
