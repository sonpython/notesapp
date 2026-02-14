"""Shared FastAPI dependencies for authentication and database access."""

from __future__ import annotations

import logging

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import get_db as _get_db

logger = logging.getLogger(__name__)

# Re-export get_db so callers can import from app.deps
get_db = _get_db

# Bearer token scheme used to extract the JWT from the Authorization header
_bearer_scheme = HTTPBearer()

_JWT_AUDIENCE = "authenticated"

# Cache for the JWKS client to avoid re-fetching keys on every request
_jwks_client: pyjwt.PyJWKClient | None = None


def _get_jwks_client() -> pyjwt.PyJWKClient:
    """Return a cached PyJWKClient that fetches keys from Supabase."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = pyjwt.PyJWKClient(jwks_url)
    return _jwks_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Validate the Supabase JWT and return the authenticated user's ID.

    Supports both ES256 (JWKS) and HS256 (JWT secret) tokens.

    Raises:
        HTTPException: 401 if the token is missing, expired, or invalid.
    """
    token = credentials.credentials

    try:
        # Check token algorithm to decide verification method
        header = pyjwt.get_unverified_header(token)
        alg = header.get("alg", "")

        if alg.startswith("ES") or alg.startswith("RS") or alg.startswith("PS"):
            # Asymmetric — use JWKS public key from Supabase
            client = _get_jwks_client()
            signing_key = client.get_signing_key_from_jwt(token)
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience=_JWT_AUDIENCE,
            )
        else:
            # Symmetric (HS256/HS384/HS512) — use JWT secret
            payload = pyjwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256", "HS384", "HS512"],
                audience=_JWT_AUDIENCE,
            )
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
