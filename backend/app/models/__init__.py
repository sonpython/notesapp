"""SQLAlchemy ORM models for the NotesApp backend.

Import all models here so that ``Base.metadata`` is fully populated when
Alembic or application startup inspects it.
"""

from app.database import Base
from app.models.folder import Folder
from app.models.note import Note
from app.models.tag import NoteTag, Tag, TodoTag
from app.models.telegram import TelegramSettings
from app.models.todo import Todo

__all__ = [
    "Base",
    "Folder",
    "Note",
    "NoteTag",
    "Tag",
    "Todo",
    "TodoTag",
    "TelegramSettings",
]
