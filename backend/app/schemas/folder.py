from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FolderCreate(BaseModel):
    name: str
    parent_id: UUID | None = None
    icon: str | None = None


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: UUID | None = None
    icon: str | None = None


class FolderResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    parent_id: UUID | None
    icon: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class FolderTreeResponse(FolderResponse):
    children: list["FolderTreeResponse"] = []
