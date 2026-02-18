"""WebAuthn login endpoints for passkey authentication."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.auth import AuthOptionsResponse, AuthResponse, LoginVerifyRequest
from app.services.jwt_service import create_jwt, set_session_cookie
from app.services.webauthn_service import create_authentication_options, verify_authentication

router = APIRouter(prefix="/api/auth/login", tags=["auth"])


@router.post("/options", response_model=AuthOptionsResponse)
async def login_options(
    db: AsyncSession = Depends(get_db),
) -> AuthOptionsResponse:
    """Generate WebAuthn authentication options.

    Returns PublicKeyCredentialRequestOptions for the browser to request a passkey.
    Uses discoverable credentials (no allowCredentials list).
    """
    options, challenge_id = await create_authentication_options(db)
    return AuthOptionsResponse(options=options, challenge_id=challenge_id)


@router.post("/verify", response_model=AuthResponse)
async def login_verify(
    request: LoginVerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Verify WebAuthn authentication and issue session.

    Validates the passkey assertion and issues a session JWT cookie.
    """
    try:
        user = await verify_authentication(db, request.credential, request.challenge_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Issue JWT and set cookie
    token = create_jwt(str(user.id))
    set_session_cookie(response, token)

    return AuthResponse(user_id=str(user.id), display_name=user.display_name)
