"""WebAuthn registration endpoints for passkey creation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_db
from app.schemas.auth import AuthOptionsResponse, AuthResponse, RegisterOptionsRequest, RegisterVerifyRequest
from app.services.jwt_service import create_jwt, set_session_cookie
from app.services.webauthn_service import create_registration_options, verify_registration

router = APIRouter(prefix="/api/auth/register", tags=["auth"])


@router.post("/options", response_model=AuthOptionsResponse)
async def register_options(
    request: RegisterOptionsRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthOptionsResponse:
    """Generate WebAuthn registration options.

    Returns PublicKeyCredentialCreationOptions for the browser to create a passkey.
    """
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently closed. Please contact admin.",
        )
    options, challenge_id = await create_registration_options(db, request.display_name)
    return AuthOptionsResponse(options=options, challenge_id=challenge_id)


@router.post("/verify", response_model=AuthResponse)
async def register_verify(
    request: RegisterVerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Verify WebAuthn registration and create user account.

    Creates the user and passkey credential, then issues a session JWT cookie.
    """
    try:
        user, _ = await verify_registration(db, request.credential, request.challenge_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Issue JWT and set cookie
    token = create_jwt(str(user.id))
    set_session_cookie(response, token)

    return AuthResponse(user_id=str(user.id), display_name=user.display_name)
