"""FastMCP middleware translating Temporal RPC failures into registry errors."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware

from temporal_mcp.errors import IncomingAuthPolicyDeniedError, TemporalMcpError
from temporal_mcp.errors.rpc_translation import find_rpc_error, translate_rpc_error


if TYPE_CHECKING:
    from typing import Any  # Required to match FastMCP Middleware.on_request signature.

    from fastmcp.server.auth import AccessToken
    from fastmcp.server.middleware import CallNext, MiddlewareContext
    from fastmcp.tools import ToolResult
    from mcp import types as mt
    from mcp.types import CallToolRequestParams

    from temporal_mcp.services.auth_policy import ClaimExpressionPolicy


logger = logging.getLogger(__name__)


class ClaimExpressionMiddleware(Middleware):
    """Authorize MCP requests with a CEL expression against JWT claims."""

    def __init__(self, policy: ClaimExpressionPolicy) -> None:
        """Initialize with the compiled claim expression policy.

        Args:
            policy: CEL policy evaluated against verified JWT claims.
        """
        self._policy = policy

    async def on_request(
        self,
        context: MiddlewareContext[mt.Request[Any, Any]],
        call_next: CallNext[mt.Request[Any, Any], Any],
    ) -> Any:  # noqa: ANN401 - FastMCP's base hook requires this return type.
        """Authorize a client request before continuing the middleware chain.

        Args:
            context: Middleware context carrying the MCP request.
            call_next: Continuation running the rest of the chain.

        Returns:
            The result from the rest of the chain.

        Raises:
            IncomingAuthPolicyDeniedError: If the caller claims do not satisfy
                the configured claim expression.
        """
        access_token = get_access_token()
        allowed = access_token is not None and self._policy.allows(access_token.claims)
        _log_claim_policy_decision(self._policy.expression, access_token, allowed=allowed)
        if not allowed:
            raise IncomingAuthPolicyDeniedError
        return await call_next(context)


class TemporalRpcErrorMiddleware(Middleware):
    """Translate RPCError causes of tool failures into registry ToolErrors.

    FastMCP wraps tool exceptions (masked or not) with the original error kept
    in __cause__; this middleware unwraps that chain so clients receive clear,
    non-sensitive messages for client-actionable gRPC statuses.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[CallToolRequestParams],
        call_next: CallNext[CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Run the tool call, translating RPC failures to registry errors.

        Args:
            context: Middleware context carrying the tool call params.
            call_next: Continuation running the rest of the chain.

        Returns:
            The tool result from the rest of the chain.

        Raises:
            TemporalRpcError: When the failure is a client-actionable RPC error.
        """
        try:
            return await call_next(context)
        except TemporalMcpError:
            raise
        except Exception as err:
            rpc = find_rpc_error(err)
            domain = translate_rpc_error(rpc) if rpc is not None else None
            if rpc is None or domain is None:
                raise
            logger.warning(
                "RPC failure in tool %r translated to %s (status %s): %s",
                context.message.name,
                type(domain).__name__,
                domain.status_name,
                rpc.message,
            )
            raise domain from rpc


def _log_claim_policy_decision(
    expression: str,
    access_token: AccessToken | None,
    *,
    allowed: bool,
) -> None:
    """Log a safe incoming claim-policy decision summary."""
    action = "allowed" if allowed else "denied"
    logger.info(
        "Incoming claim expression %s request: expression=%r subject=%r client_id=%r claim_keys=%s",
        action,
        expression,
        _token_subject(access_token),
        _token_client_id(access_token),
        _claim_keys(access_token),
    )


def _token_subject(access_token: AccessToken | None) -> str | None:
    """Return the caller subject claim when present."""
    if access_token is None:
        return None
    subject = access_token.claims.get("subject") or access_token.claims.get("sub")
    return str(subject) if subject is not None else None


def _token_client_id(access_token: AccessToken | None) -> str | None:
    """Return the verified client id when present."""
    return access_token.client_id if access_token is not None else None


def _claim_keys(access_token: AccessToken | None) -> list[str]:
    """Return sorted claim keys without logging claim values."""
    if access_token is None:
        return []
    return sorted(access_token.claims)
