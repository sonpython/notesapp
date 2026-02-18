"""Shared FastAPI dependencies for authentication and database access."""

from __future__ import annotations

import logging

import jwt as pyjwt
from fastapi import HTTPException, Request, status

from app.config import settings
from app.database import get_db as _get_db
from app.services.jwt_service import decode_jwt

logger = logging.getLogger(__name__)

# Re-export get_db so callers can import from app.deps
get_db = _get_db


async def get_current_user(request: Request) -> str:
    """Validate the JWT from cookie or Bearer header and return the user ID.

    Checks:
    1. Session cookie (HttpOnly, set by login/register)
    2. Authorization: Bearer header (for API clients, mobile, etc.)

    Raises:
        HTTPException: 401 if no token, or token is invalid/expired.
    """
    token: str | None = None

    # 1. Try session cookie first
    token = request.cookies.get("session")

    # 2. Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_jwt(token)
    except pyjwt.PyJWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id
