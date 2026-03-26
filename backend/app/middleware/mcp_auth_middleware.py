"""Pure ASGI middleware to authenticate MCP requests via API key.

Uses raw ASGI instead of BaseHTTPMiddleware to avoid breaking
SQLAlchemy's greenlet async context in downstream handlers.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from starlette.types import ASGIApp, Receive, Scope, Send

from app.database import async_session_factory
from app.models.api_key import ApiKey


class McpAuthMiddleware:
    """Validates API key for /mcp/* routes, injects user_id into ASGI state."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/mcp"):
            await self.app(scope, receive, send)
            return

        # Extract API key from query string or Authorization header
        api_key = self._get_api_key(scope)
        if not api_key:
            await self._send_json_error(
                send, "Missing auth. Use ?api_key=xxx or Bearer header", 401
            )
            return

        user_id = await self._resolve_user_id(api_key)
        if not user_id:
            await self._send_json_error(send, "Invalid or expired API key.", 401)
            return

        # Inject user_id into ASGI scope state for downstream access
        scope.setdefault("state", {})["mcp_user_id"] = user_id

        await self.app(scope, receive, send)

    @staticmethod
    def _get_api_key(scope: Scope) -> str | None:
        # Check query params
        qs = scope.get("query_string", b"").decode()
        for param in qs.split("&"):
            if param.startswith("api_key="):
                return param[8:]

        # Check Authorization header
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                decoded = value.decode()
                if decoded.startswith("Bearer "):
                    return decoded[7:]
        return None

    @staticmethod
    async def _resolve_user_id(api_key: str) -> str | None:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        from sqlalchemy import select

        async with async_session_factory() as session:
            stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                return None
            if row.expires_at and row.expires_at < datetime.now(UTC):
                return None

            row.last_used_at = datetime.now(UTC)
            await session.commit()
            return str(row.user_id)

    @staticmethod
    async def _send_json_error(send: Send, message: str, status: int) -> None:
        body = json.dumps({"error": message}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body)).encode()],
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
