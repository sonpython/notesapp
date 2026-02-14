"""Pydantic schemas for tag CRUD operations."""

from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
import re


class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str
    color: str = "#6b7280"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 50:
            raise ValueError("Tag name must be 1-50 characters")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be hex format #xxxxxx")
        return v.lower()


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: str | None = None
    color: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v or len(v) > 50:
                raise ValueError("Tag name must be 1-50 characters")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be hex format #xxxxxx")
        return v.lower() if v else v


class TagResponse(BaseModel):
    """Schema for tag responses."""
    id: UUID
    user_id: UUID
    name: str
    color: str
    created_at: datetime
    model_config = {"from_attributes": True}


class TagAttachRequest(BaseModel):
    """Schema for attaching tags to notes/todos."""
    tag_ids: list[UUID]
