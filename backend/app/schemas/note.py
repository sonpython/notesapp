from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

# Forward reference for TagResponse
if False:
    from app.schemas.tag import TagResponse


class NoteCreate(BaseModel):
    title: str = ""
    content: str = ""
    folder_id: UUID | None = None
    is_pinned: bool = False
    tag_ids: list[UUID] | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    folder_id: UUID | None = None  # Use special sentinel for "remove from folder"
    is_pinned: bool | None = None
    is_archived: bool | None = None
    tag_ids: list[UUID] | None = None


class NoteResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: str
    folder_id: UUID | None
    is_pinned: bool
    is_archived: bool
    is_shared: bool = False
    created_at: datetime
    updated_at: datetime
    tags: list["TagResponse"] = []
    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Lighter response for listing (no full content)"""
    id: UUID
    title: str
    content: str  # First 200 chars preview
    folder_id: UUID | None
    is_pinned: bool
    is_archived: bool
    is_shared: bool = False
    created_at: datetime
    updated_at: datetime
    tags: list["TagResponse"] = []
    model_config = {"from_attributes": True}


# Resolve forward references
from app.schemas.tag import TagResponse
NoteResponse.model_rebuild()
NoteListResponse.model_rebuild()
