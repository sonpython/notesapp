"""Auth router -- user session management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import AuthResponse
from app.services.jwt_service import clear_session_cookie

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=AuthResponse)
async def get_me(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Return the authenticated user's info."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return AuthResponse(user_id=str(user.id), display_name=user.display_name)


@router.post("/logout")
async def logout(response: Response) -> dict:
    """Clear the session cookie and log out."""
    clear_session_cookie(response)
    return {"ok": True}
