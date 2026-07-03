"""Base exception for the Temporal MCP server."""

from __future__ import annotations

from fastmcp.exceptions import ToolError


class TemporalMcpError(ToolError):
    """Base class for all application errors.

    Inherits ToolError so domain messages reach MCP clients even when the server
    masks unexpected error details.
    """

    def __init__(self, message: str) -> None:
        """Initialize with a human-readable message.

        Args:
            message: Error message (English).
        """
        super().__init__(message)
        self.message = message


class TemporalRpcError(TemporalMcpError):
    """Base for Temporal RPC failures translated from gRPC statuses."""

    def __init__(self, message: str, *, status_name: str, detail: str) -> None:
        """Initialize with the rendered message and RPC context.

        Args:
            message: Rendered client-facing message.
            status_name: gRPC status name (e.g. "NOT_FOUND").
            detail: Raw server-provided error text.
        """
        super().__init__(message)
        self.status_name = status_name
        self.detail = detail
