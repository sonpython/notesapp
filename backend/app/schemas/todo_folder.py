from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TodoFolderCreate(BaseModel):
    name: str
    parent_id: UUID | None = None
    sort_order: int = 0


class TodoFolderUpdate(BaseModel):
    name: str | None = None
    parent_id: UUID | None = None
    sort_order: int | None = None


class TodoFolderResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    parent_id: UUID | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TodoFolderStatsResponse(BaseModel):
    folder_id: UUID
    total: int
    completed: int
    completion_pct: int  # 0-100
