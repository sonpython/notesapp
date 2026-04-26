"""FastAPI dependencies for public folder share endpoints.

Resolves and validates the SharedTodoFolder by pub_id, enforces expiry/view
limits, and parses the share session cookie when present. Returns a small
context object the routers can use for authorization checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import jwt as pyjwt
from fastapi import Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.shared_todo_folder import SharedTodoFolder
from app.services.share_session_service import decode_share_session, share_cookie_name


@dataclass(slots=True)
class ShareFolderContext:
    """Resolved context for a public share request."""

    share: SharedTodoFolder
    has_session: bool
    session_is_editable: bool


def _enforce_share_validity(share: SharedTodoFolder) -> None:
    """Raise 410 Gone if expired or view limit exceeded."""
    if share.expires_at and datetime.now(UTC) > share.expires_at:
        raise HTTPException(status_code=410, detail="This share has expired")
    if share.max_views is not None and share.view_count >= share.max_views:
        raise HTTPException(status_code=410, detail="This share has reached its view limit")


async def load_share_folder(
    pub_id: str = Path(..., min_length=6, max_length=6),
    db: AsyncSession = Depends(get_db),
) -> SharedTodoFolder:
    """Load the SharedTodoFolder by pub_id and enforce expiry / view limit.

    No session check -- used by /check before issuing a session.
    """
    stmt = select(SharedTodoFolder).where(SharedTodoFolder.pub_id == pub_id)
    result = await db.execute(stmt)
    share = result.scalar_one_or_none()
    if share is None:
        raise HTTPException(status_code=404, detail="Shared folder not found")
    _enforce_share_validity(share)
    return share


async def require_share_session(
    request: Request,
    share: SharedTodoFolder = Depends(load_share_folder),
) -> ShareFolderContext:
    """Require a valid share session cookie for the given pub_id.

    Allowed for unprotected shares with no password too -- in that case the
    /access endpoint will still have issued a session on first visit. The
    rule is uniform: any data endpoint past /check requires the cookie.
    """
    cookie_value = request.cookies.get(share_cookie_name(share.pub_id))
    if not cookie_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Share session required",
        )
    try:
        payload = decode_share_session(cookie_value, share.pub_id)
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired share session",
        )

    return ShareFolderContext(
        share=share,
        has_session=True,
        session_is_editable=bool(payload.get("is_editable", False)),
    )


def require_editable(
    ctx: ShareFolderContext = Depends(require_share_session),
) -> ShareFolderContext:
    """Require both a valid session AND the share itself to be editable.

    Both gates matter: the cookie carries the editable flag captured at
    /access time, but if the owner toggles `is_editable` off afterwards we
    refuse based on the current DB value too.
    """
    if not ctx.share.is_editable or not ctx.session_is_editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This share is read-only",
        )
    return ctx
