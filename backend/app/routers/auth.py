"""Auth router -- simple user verification endpoint."""

from fastapi import APIRouter, Depends

from app.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)) -> dict:
    """Return the authenticated user's ID as a simple verification."""
    return {"user_id": user_id}
