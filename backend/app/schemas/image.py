"""Pydantic schemas for image upload API."""

from __future__ import annotations

from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    """Response after successful image upload."""

    id: str
    url: str
    filename: str
    content_type: str
    size: int


class ImageListItem(BaseModel):
    """Single image in list response."""

    id: str
    url: str
    size: int
    last_modified: str | None = None
