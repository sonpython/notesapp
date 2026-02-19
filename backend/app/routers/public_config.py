"""Public configuration endpoints (no auth required)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


class PublicConfigResponse(BaseModel):
    """Public configuration exposed to the frontend."""

    allow_registration: bool


@router.get("/public", response_model=PublicConfigResponse)
async def get_public_config() -> PublicConfigResponse:
    """Return public configuration settings."""
    return PublicConfigResponse(allow_registration=settings.ALLOW_REGISTRATION)
