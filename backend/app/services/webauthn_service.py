"""WebAuthn service for passkey registration and authentication ceremonies."""

from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import settings
from app.models.passkey_credential import PasskeyCredential
from app.models.user import User
from app.models.webauthn_challenge import WebAuthnChallenge

logger = logging.getLogger(__name__)

CHALLENGE_TTL_MINUTES = 5


async def create_registration_options(
    db: AsyncSession,
    display_name: str,
) -> tuple[dict, str]:
    """Generate WebAuthn registration options and store challenge.

    Args:
        db: Database session.
        display_name: User's display name for the passkey.

    Returns:
        Tuple of (options_dict, challenge_id).
    """
    # Generate a temporary user_id for the new user
    temp_user_id = uuid.uuid4()

    options = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=temp_user_id.bytes,
        user_name=display_name,
        user_display_name=display_name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    # Store challenge in DB (base64 encode binary challenge)
    challenge_b64 = base64.urlsafe_b64encode(options.challenge).decode("ascii") if isinstance(options.challenge, bytes) else options.challenge
    challenge_record = WebAuthnChallenge(
        challenge=challenge_b64,
        user_id=temp_user_id,
        display_name=display_name,
        type="register",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=CHALLENGE_TTL_MINUTES),
    )
    db.add(challenge_record)
    await db.commit()
    await db.refresh(challenge_record)

    # Convert options to JSON-serializable dict
    options_json = json.loads(options_to_json(options))

    return options_json, str(challenge_record.id)


async def verify_registration(
    db: AsyncSession,
    credential_json: dict,
    challenge_id: str,
) -> tuple[User, PasskeyCredential]:
    """Verify WebAuthn registration response and create user + credential.

    Args:
        db: Database session.
        credential_json: The registration response from the browser.
        challenge_id: The challenge ID to validate against.

    Returns:
        Tuple of (created User, created PasskeyCredential).

    Raises:
        ValueError: If challenge is invalid, expired, or verification fails.
    """
    # Fetch and delete challenge (single-use)
    challenge_record = await _get_and_delete_challenge(db, challenge_id, "register")

    try:
        # Decode base64 challenge back to bytes
        expected_challenge = base64.urlsafe_b64decode(challenge_record.challenge) if isinstance(challenge_record.challenge, str) else challenge_record.challenge
        verification = verify_registration_response(
            credential=credential_json,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_ORIGIN,
        )
    except Exception as e:
        logger.warning("Registration verification failed: %s", e)
        raise ValueError(f"Registration verification failed: {e}")

    # Create user
    user = User(
        id=challenge_record.user_id,
        display_name=challenge_record.display_name or "User",
    )
    db.add(user)

    # Create passkey credential
    credential = PasskeyCredential(
        user_id=user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=json.dumps(credential_json.get("response", {}).get("transports", [])),
        backed_up=verification.credential_backed_up,
        device_type=verification.credential_device_type,
    )
    db.add(credential)

    await db.commit()
    await db.refresh(user)
    await db.refresh(credential)

    return user, credential


async def create_authentication_options(db: AsyncSession) -> tuple[dict, str]:
    """Generate WebAuthn authentication options for discoverable credentials.

    Args:
        db: Database session.

    Returns:
        Tuple of (options_dict, challenge_id).
    """
    options = generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        user_verification=UserVerificationRequirement.PREFERRED,
        # No allow_credentials = discoverable credential flow
    )

    # Store challenge in DB (base64 encode binary challenge)
    challenge_b64 = base64.urlsafe_b64encode(options.challenge).decode("ascii") if isinstance(options.challenge, bytes) else options.challenge
    challenge_record = WebAuthnChallenge(
        challenge=challenge_b64,
        user_id=None,
        type="login",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=CHALLENGE_TTL_MINUTES),
    )
    db.add(challenge_record)
    await db.commit()
    await db.refresh(challenge_record)

    options_json = json.loads(options_to_json(options))

    return options_json, str(challenge_record.id)


async def verify_authentication(
    db: AsyncSession,
    credential_json: dict,
    challenge_id: str,
) -> User:
    """Verify WebAuthn authentication response.

    Args:
        db: Database session.
        credential_json: The authentication response from the browser.
        challenge_id: The challenge ID to validate against.

    Returns:
        The authenticated User.

    Raises:
        ValueError: If challenge is invalid, credential not found, or verification fails.
    """
    # Fetch and delete challenge (single-use)
    challenge_record = await _get_and_delete_challenge(db, challenge_id, "login")

    # Look up credential by credential_id
    credential_id_bytes = _base64url_to_bytes(credential_json.get("id", ""))
    result = await db.execute(
        select(PasskeyCredential).where(PasskeyCredential.credential_id == credential_id_bytes)
    )
    stored_credential = result.scalar_one_or_none()

    if not stored_credential:
        raise ValueError("Credential not found")

    try:
        # Decode base64 challenge back to bytes
        expected_challenge = base64.urlsafe_b64decode(challenge_record.challenge) if isinstance(challenge_record.challenge, str) else challenge_record.challenge
        verification = verify_authentication_response(
            credential=credential_json,
            expected_challenge=expected_challenge,
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_ORIGIN,
            credential_public_key=stored_credential.public_key,
            credential_current_sign_count=stored_credential.sign_count,
        )
    except Exception as e:
        logger.warning("Authentication verification failed: %s", e)
        raise ValueError(f"Authentication verification failed: {e}")

    # Update sign_count
    stored_credential.sign_count = verification.new_sign_count
    await db.commit()

    # Fetch and return user
    result = await db.execute(select(User).where(User.id == stored_credential.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found for credential")

    return user


async def cleanup_expired_challenges(db: AsyncSession) -> int:
    """Delete expired challenge records.

    Args:
        db: Database session.

    Returns:
        Number of deleted records.
    """
    result = await db.execute(
        delete(WebAuthnChallenge).where(WebAuthnChallenge.expires_at < datetime.now(timezone.utc))
    )
    await db.commit()
    return result.rowcount


async def _get_and_delete_challenge(
    db: AsyncSession,
    challenge_id: str,
    expected_type: str,
) -> WebAuthnChallenge:
    """Fetch and delete a challenge record (single-use).

    Args:
        db: Database session.
        challenge_id: The challenge ID to fetch.
        expected_type: Expected challenge type ('register' or 'login').

    Returns:
        The challenge record.

    Raises:
        ValueError: If challenge not found, expired, or wrong type.
    """
    try:
        challenge_uuid = uuid.UUID(challenge_id)
    except ValueError:
        raise ValueError("Invalid challenge ID format")

    result = await db.execute(
        select(WebAuthnChallenge).where(WebAuthnChallenge.id == challenge_uuid)
    )
    challenge = result.scalar_one_or_none()

    if not challenge:
        raise ValueError("Challenge not found")

    if challenge.type != expected_type:
        raise ValueError(f"Challenge type mismatch: expected {expected_type}, got {challenge.type}")

    if challenge.expires_at < datetime.now(timezone.utc):
        await db.delete(challenge)
        await db.commit()
        raise ValueError("Challenge expired")

    # Delete challenge (single-use)
    await db.delete(challenge)
    await db.commit()

    return challenge


def _base64url_to_bytes(data: str) -> bytes:
    """Convert base64url-encoded string to bytes."""
    import base64

    # Add padding if needed
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    # Replace URL-safe chars
    data = data.replace("-", "+").replace("_", "/")
    return base64.b64decode(data)
