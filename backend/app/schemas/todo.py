from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    deadline: datetime | None = None
    parent_id: UUID | None = None
    note_id: UUID | None = None
    priority: int = 0  # 0=none, 1=low, 2=medium, 3=high
    sort_order: int = 0
    reminder_at: datetime | None = None


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
    priority: int
    sort_order: int
    reminder_at: datetime | None
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TodoWithChildrenResponse(TodoResponse):
    children: list["TodoWithChildrenResponse"] = []
