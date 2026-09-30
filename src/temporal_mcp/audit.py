"""Record tool calls without logging arguments, results, or credentials."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING

from fastmcp.server.dependencies import get_access_token, get_http_request
from fastmcp.server.middleware import Middleware


if TYPE_CHECKING:
    from fastmcp.server.middleware import CallNext, MiddlewareContext
    from fastmcp.tools import ToolResult
    from mcp.types import CallToolRequestParams


logger = logging.getLogger(__name__)


def current_user(trusted_user_header: str | None = None) -> str:
    """Resolve a verified identity or an explicitly trusted proxy header.

    Args:
        trusted_user_header: Header set and sanitized by an authenticated proxy.

    Returns:
        The username, token subject, client ID, or anonymous fallback.
    """
    token = get_access_token()
    if token is not None:
        identity = token.claims.get("preferred_username") or token.claims.get("sub") or token.subject or token.client_id
        return str(identity)
    if trusted_user_header:
        try:
            request = get_http_request()
        except RuntimeError:
            return "anonymous"
        else:
            return request.headers.get(trusted_user_header, "").strip() or "anonymous"
    return "anonymous"


class AuditMiddleware(Middleware):
    """Emit one JSON audit record per tool invocation to the application logger."""

    def __init__(self, trusted_user_header: str | None = None) -> None:
        """Initialize audit identity resolution.

        Args:
            trusted_user_header: Optional trusted proxy username header.
        """
        self._trusted_user_header = trusted_user_header

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Record the outcome and duration while preserving tool behavior.

        Args:
            context: Tool invocation context.
            call_next: Remaining middleware and tool handler.

        Returns:
            The original tool result. Handler exceptions propagate unchanged.
        """
        started = time.monotonic()
        try:
            result = await call_next(context)
        except asyncio.CancelledError:
            self._log(context.message, started, outcome="cancelled")
            raise
        except Exception as error:
            self._log(context.message, started, outcome=f"error:{type(error).__name__}")
            raise
        else:
            self._log(context.message, started, outcome="error" if result.is_error else "ok")
            return result

    def _log(self, message: CallToolRequestParams, started: float, *, outcome: str) -> None:
        """Write a JSON record with identity and execution metadata only."""
        arguments = message.arguments or {}
        target = arguments.get("name") if message.name == "call_tool" else None
        record = {
            "user": current_user(self._trusted_user_header),
            "tool": message.name,
            "outcome": outcome,
            "duration_ms": round((time.monotonic() - started) * 1000),
        }
        if isinstance(target, str):
            record["target_tool"] = target
        logger.info(json.dumps(record, ensure_ascii=True))
