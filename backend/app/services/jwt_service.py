"""JWT service for creating and validating session tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Response

from app.config import settings


def create_jwt(user_id: str) -> str:
    """Create HS256 JWT with user_id as subject.

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        Encoded JWT string.
    """
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRY_DAYS),
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


def set_session_cookie(response: Response, token: str) -> None:
    """Set HttpOnly session cookie on response.

    Args:
        response: FastAPI Response object.
        token: The JWT token to set as cookie.
    """
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=settings.WEBAUTHN_ORIGIN.startswith("https"),
        samesite="lax",
        max_age=settings.JWT_EXPIRY_DAYS * 86400,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Delete session cookie.

    Args:
        response: FastAPI Response object.
    """
    response.delete_cookie(key="session", path="/")
