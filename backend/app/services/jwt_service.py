"""JWT service for creating and validating session tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Response

from app.config import settings


def create_jwt(user_id: str, expiry_days: int | None = None) -> str:
    """Create HS256 JWT with user_id as subject.

    Args:
        user_id: The UUID of the authenticated user.
        expiry_days: Override expiry in days. Defaults to settings.JWT_EXPIRY_DAYS.

    Returns:
        Encoded JWT string.
    """
    days = expiry_days if expiry_days is not None else settings.JWT_EXPIRY_DAYS
    payload = {
        "sub": user_id,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(days=days),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_jwt(token: str) -> dict:
    """Decode and validate HS256 JWT.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dictionary.

    Raises:
        jwt.PyJWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])


def set_session_cookie(response: Response, token: str, expiry_days: int | None = None) -> None:
    """Set HttpOnly session cookie on response.

    Args:
        response: FastAPI Response object.
        token: The JWT token to set as cookie.
        expiry_days: Override expiry in days. Defaults to settings.JWT_EXPIRY_DAYS.
    """
    days = expiry_days if expiry_days is not None else settings.JWT_EXPIRY_DAYS
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=settings.WEBAUTHN_ORIGIN.startswith("https"),
        samesite="lax",
        max_age=days * 86400,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Delete session cookie.

    Args:
        response: FastAPI Response object.
    """
    response.delete_cookie(key="session", path="/")
