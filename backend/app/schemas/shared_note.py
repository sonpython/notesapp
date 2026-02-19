"""Schemas for shared note endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ShareNoteRequest(BaseModel):
    """Request to create a shared link for a note."""

    password: str | None = Field(None, description="Optional password protection")
    expires_in_hours: int | None = Field(None, ge=1, le=720, description="Hours until expiry (max 30 days)")
    max_views: int | None = Field(None, ge=1, le=1000, description="Max view count")


class ShareNoteResponse(BaseModel):
    """Response with the share link info."""

    pub_id: str
    url: str
    has_password: bool
    expires_at: datetime | None
    max_views: int | None
    view_count: int
    created_at: datetime


class SharedNoteViewResponse(BaseModel):
    """Public view of a shared note."""

    title: str
    content: str
    created_at: datetime
    updated_at: datetime


class SharedNotePasswordRequest(BaseModel):
    """Request to verify password for a shared note."""

    password: str
