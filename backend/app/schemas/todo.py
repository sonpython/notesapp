from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# Forward reference for TagResponse
if False:
    from app.schemas.tag import TagResponse


class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime | None = None
    parent_id: UUID | None = None
    note_id: UUID | None = None
    priority: int = 0  # 0=none, 1=low, 2=medium, 3=high
    sort_order: int = 0
    reminder_at: datetime | None = None
    recurrence_type: str | None = None  # daily, weekly, monthly, custom
    recurrence_interval: int | None = None
    recurrence_days: str | None = None
    recurrence_end_date: datetime | None = None
    tag_ids: list[UUID] | None = None
    folder_id: UUID | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None
    deadline: datetime | None = None
    parent_id: UUID | None = None
    note_id: UUID | None = None
    priority: int | None = None
    sort_order: int | None = None
    reminder_at: datetime | None = None
    recurrence_type: str | None = None
    recurrence_interval: int | None = None
    recurrence_days: str | None = None
    recurrence_end_date: datetime | None = None
    tag_ids: list[UUID] | None = None
    folder_id: UUID | None = None


class TodoResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    is_completed: bool
    completed_at: datetime | None
    deadline: datetime | None
    parent_id: UUID | None
    note_id: UUID | None
    folder_id: UUID | None
    priority: int
    sort_order: int
    reminder_at: datetime | None
    reminder_sent: bool
    recurrence_type: str | None
    recurrence_interval: int | None
    recurrence_days: str | None
    recurrence_end_date: datetime | None
    recurrence_parent_id: UUID | None
    created_at: datetime
    updated_at: datetime
    tags: list["TagResponse"] = []
    model_config = {"from_attributes": True}


class TodoWithChildrenResponse(TodoResponse):
    children: list["TodoWithChildrenResponse"] = []


class TodoReorderItem(BaseModel):
    """Single item in reorder request"""

    id: UUID
    sort_order: int


class TodoReorderRequest(BaseModel):
    """Batch reorder request"""

    items: list[TodoReorderItem]


# Resolve forward references
from app.schemas.tag import TagResponse

TodoResponse.model_rebuild()
TodoWithChildrenResponse.model_rebuild()
