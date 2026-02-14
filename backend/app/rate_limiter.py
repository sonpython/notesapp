"""Rate limiting configuration using slowapi.

Provides different rate limiters for different endpoint types:
- auth_limiter: Strict limits for login/signup (5/min)
- webhook_limiter: Moderate limits for telegram webhook (30/min)
- default_limiter: Standard limits for authenticated endpoints (60/min)
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _get_rate_limit_key(request) -> str:
    """Get rate limit key from request.

    For authenticated requests, use user_id from state.
    Falls back to IP address for unauthenticated requests.
    """
    # Try to get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


# Main limiter instance with IP-based key
limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
)

# Rate limit strings for decorators
AUTH_RATE_LIMIT = settings.RATE_LIMIT_AUTH
WEBHOOK_RATE_LIMIT = settings.RATE_LIMIT_WEBHOOK
DEFAULT_RATE_LIMIT = settings.RATE_LIMIT_DEFAULT
