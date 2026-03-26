"""API keys router — CRUD for user API keys (MCP authentication)."""

from __future__ import annotations

import hashlib
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])

# Key format: na_<40 random hex chars> (total 43 chars, prefix "na_")
KEY_PREFIX = "na_"
KEY_RANDOM_BYTES = 20  # 40 hex chars


def _generate_key() -> tuple[str, str, str]:
    """Generate API key, return (plaintext_key, sha256_hash, display_prefix)."""
    random_part = secrets.token_hex(KEY_RANDOM_BYTES)
    plaintext = f"{KEY_PREFIX}{random_part}"
    key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
    display_prefix = f"{KEY_PREFIX}{random_part[:8]}..."
    return plaintext, key_hash, display_prefix


def _hash_key(plaintext: str) -> str:
    """Hash a plaintext API key."""
    return hashlib.sha256(plaintext.encode()).hexdigest()


@router.get("/", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ApiKeyResponse]:
    """List all API keys for the current user (without full key values)."""
    stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("/", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    """Create a new API key. The full key is returned ONLY in this response."""
    plaintext, key_hash, display_prefix = _generate_key()

    api_key = ApiKey(
        user_id=user_id,
        name=body.name,
        key_hash=key_hash,
        key_prefix=display_prefix,
        expires_at=body.expires_at,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=plaintext,
        key_prefix=display_prefix,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: UUID,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete an API key."""
    api_key = await session.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    if str(api_key.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await session.delete(api_key)
    await session.commit()
