"""Short-lived JWT cookie service for unauthenticated public folder share sessions.

Issued by `POST /api/pub/folder/{pub_id}/access` after password verify.
Used by all subsequent public endpoints to skip re-prompting the password
on every request. Cookie is HttpOnly, scoped to the pub_id, expires in 2h.

The cookie name is per-pub_id so multiple shared folders can be open in the
same browser without interfering with each other.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Response

from app.config import settings

SHARE_SESSION_TTL_HOURS = 2
SHARE_SESSION_AUDIENCE = "share_session_todo_folder"


def share_cookie_name(pub_id: str) -> str:
    """Cookie name unique to a given pub_id (avoids cross-share collision)."""
    return f"share_session_{pub_id}"


def issue_share_session(response: Response, pub_id: str, is_editable: bool) -> str:
    """Encode a JWT and set it as an HttpOnly cookie scoped to pub_id."""
    now = datetime.now(UTC)
    payload = {
        "sub": pub_id,
        "aud": SHARE_SESSION_AUDIENCE,
        "is_editable": bool(is_editable),
        "iat": now,
        "exp": now + timedelta(hours=SHARE_SESSION_TTL_HOURS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    response.set_cookie(
        key=share_cookie_name(pub_id),
        value=token,
        httponly=True,
        secure=settings.WEBAUTHN_ORIGIN.startswith("https"),
        samesite="lax",
        max_age=SHARE_SESSION_TTL_HOURS * 3600,
        path="/",
    )
    return token


def decode_share_session(token: str, expected_pub_id: str) -> dict:
    """Decode and validate the share session JWT.

    Raises:
        jwt.PyJWTError on invalid/expired tokens or audience/subject mismatch.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=["HS256"],
        audience=SHARE_SESSION_AUDIENCE,
    )
    if payload.get("sub") != expected_pub_id:
        raise jwt.InvalidTokenError("pub_id mismatch")
    return payload


def clear_share_session(response: Response, pub_id: str) -> None:
    """Best-effort cookie clear (used on revocation flows if needed)."""
    response.delete_cookie(key=share_cookie_name(pub_id), path="/")
