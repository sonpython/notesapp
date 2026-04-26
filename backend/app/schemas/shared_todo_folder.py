"""Schemas for shared todo folder endpoints (owner side + public side)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# -- Owner-side -------------------------------------------------------------


class ShareTodoFolderRequest(BaseModel):
    """Owner request to create or update a folder share link."""

    password: str | None = Field(None, description="Optional password protection")
    expires_in_hours: int | None = Field(
        None, ge=1, le=720, description="Hours until expiry (max 30 days)"
    )
    max_views: int | None = Field(None, ge=1, le=1000, description="Max view count")
    is_editable: bool = Field(False, description="Allow recipients to mutate todos")


class ShareTodoFolderResponse(BaseModel):
    """Owner-facing share info."""

    pub_id: str
    url: str
    has_password: bool
    is_editable: bool
    expires_at: datetime | None
    max_views: int | None
    view_count: int
    created_at: datetime


# -- Public-side ------------------------------------------------------------


class SharedTodoFolderCheckResponse(BaseModel):
    """Public probe before unlocking."""

    requires_password: bool
    is_editable: bool
    folder_name: str


class SharedTodoFolderAccessRequest(BaseModel):
    """Public request body to access a shared folder (verifies password)."""

    password: str | None = None


class SharedFolderTodoResponse(BaseModel):
    """Public view of a single todo (subset of TodoResponse, no owner data)."""

    id: UUID
    title: str
    description: str | None
    is_completed: bool
    completed_at: datetime | None
    deadline: datetime | None
    priority: int
    sort_order: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class SharedTodoFolderViewResponse(BaseModel):
    """Public payload returned by /access -- folder meta + todos."""

    folder_name: str
    is_editable: bool
    todos: list[SharedFolderTodoResponse]


class SharedFolderTodoCreate(BaseModel):
    """Public create -- only safe fields exposed."""

    title: str
    description: str | None = None
    deadline: datetime | None = None
    priority: int = Field(0, ge=0, le=3)
    sort_order: int = 0


class SharedFolderTodoUpdate(BaseModel):
    """Public update with optimistic lock token."""

    expected_updated_at: datetime
    title: str | None = None
    description: str | None = None
    deadline: datetime | None = None
    priority: int | None = Field(None, ge=0, le=3)
    sort_order: int | None = None
    is_completed: bool | None = None


class SharedFolderTodoToggleRequest(BaseModel):
    """Public toggle requires the optimistic lock token too."""

    expected_updated_at: datetime


class SharedFolderTodoReorderItem(BaseModel):
    id: UUID
    sort_order: int


class SharedFolderTodoReorderRequest(BaseModel):
    items: list[SharedFolderTodoReorderItem]
