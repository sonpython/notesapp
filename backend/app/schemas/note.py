from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class NoteCreate(BaseModel):
    title: str = ""
    content: str = ""
    folder_id: UUID | None = None
    is_pinned: bool = False


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    folder_id: UUID | None = None  # Use special sentinel for "remove from folder"
    is_pinned: bool | None = None
    is_archived: bool | None = None


class NoteResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: str
    folder_id: UUID | None
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Lighter response for listing (no full content)"""
    id: UUID
    title: str
    content: str  # First 200 chars preview
    folder_id: UUID | None
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
