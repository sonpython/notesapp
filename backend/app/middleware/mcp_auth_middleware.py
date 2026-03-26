"""Middleware to authenticate MCP HTTP requests via API key in Authorization header."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.database import async_session_factory
from app.models.api_key import ApiKey


class McpAuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer API key for /mcp/* routes, injects user_id into request state."""

    async def dispatch(self, request: Request, call_next):
        # Only apply to /mcp routes
        if not request.url.path.startswith("/api/mcp"):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Missing or invalid Authorization header. Use: Bearer <api-key>"},
                status_code=401,
            )

        api_key = auth_header[7:]  # Strip "Bearer "
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        from sqlalchemy import select

        async with async_session_factory() as session:
            stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
            result = await session.execute(stmt)
            api_key_row = result.scalar_one_or_none()

            if api_key_row is None:
                return JSONResponse({"error": "Invalid API key."}, status_code=401)

            if api_key_row.expires_at and api_key_row.expires_at < datetime.now(UTC):
                return JSONResponse({"error": "API key has expired."}, status_code=401)

            # Update last_used_at
            api_key_row.last_used_at = datetime.now(UTC)
            await session.commit()

            # Store user_id in request state for MCP tools to access
            request.state.mcp_user_id = str(api_key_row.user_id)

        return await call_next(request)
