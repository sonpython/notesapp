"""Pydantic schemas for passkey authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterOptionsRequest(BaseModel):
    """Request body for POST /api/auth/register/options."""

    display_name: str = Field(..., min_length=1, max_length=255)


class RegisterVerifyRequest(BaseModel):
    """Request body for POST /api/auth/register/verify."""

    credential: dict  # RegistrationResponseJSON from @simplewebauthn/browser
    challenge_id: str


class LoginVerifyRequest(BaseModel):
    """Request body for POST /api/auth/login/verify."""

    credential: dict  # AuthenticationResponseJSON from @simplewebauthn/browser
    challenge_id: str


class AuthResponse(BaseModel):
    """Response for successful auth (register/login)."""

    user_id: str
    display_name: str


class AuthOptionsResponse(BaseModel):
    """Response for auth options endpoints."""

    options: dict  # PublicKeyCredentialCreationOptions or RequestOptions
    challenge_id: str
