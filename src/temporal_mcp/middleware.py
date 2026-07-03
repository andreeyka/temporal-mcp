"""FastMCP middleware translating Temporal RPC failures into registry errors."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastmcp.server.middleware import Middleware

from temporal_mcp.errors import TemporalMcpError
from temporal_mcp.errors.rpc_translation import find_rpc_error, translate_rpc_error


if TYPE_CHECKING:
    from fastmcp.server.middleware import CallNext, MiddlewareContext
    from fastmcp.tools import ToolResult
    from mcp.types import CallToolRequestParams


logger = logging.getLogger(__name__)


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
