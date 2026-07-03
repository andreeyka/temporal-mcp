"""Registry exceptions for translated Temporal RPC failures."""

from __future__ import annotations

from typing import ClassVar

from temporal_mcp.errors.base import TemporalRpcError
from temporal_mcp.errors.messages import (
    MSG_RPC_ALREADY_EXISTS,
    MSG_RPC_INVALID,
    MSG_RPC_NOT_FOUND,
    MSG_RPC_PERMISSION,
    MSG_RPC_RATE_LIMITED,
    MSG_RPC_UNAVAILABLE,
    MSG_RPC_UNSUPPORTED,
)


class _TemplatedRpcError(TemporalRpcError):
    """Intermediate base rendering the class message template from status and detail."""

    _template: ClassVar[str]

    def __init__(self, status_name: str, detail: str) -> None:
        """Initialize by rendering the class template.

        Args:
            status_name: gRPC status name observed.
            detail: Raw server-provided error text.
        """
        super().__init__(
            self._template.format(status=status_name, detail=detail),
            status_name=status_name,
            detail=detail,
        )


class UnsupportedServerFeatureError(TemporalRpcError):
    """Raised when the connected Temporal server lacks the requested RPC (UNIMPLEMENTED)."""

    def __init__(self, detail: str, *, hint: str) -> None:
        """Initialize with the server detail and an upgrade hint.

        Args:
            detail: Raw server-provided error text.
            hint: Human guidance (feature/version requirement).
        """
        super().__init__(
            MSG_RPC_UNSUPPORTED.format(detail=detail, hint=hint),
            status_name="UNIMPLEMENTED",
            detail=detail,
        )
        self.hint = hint


class TemporalNotFoundError(_TemplatedRpcError):
    """Raised when Temporal reports NOT_FOUND for the requested resource."""

    _template = MSG_RPC_NOT_FOUND

    def __init__(self, detail: str) -> None:
        """Initialize with the server detail.

        Args:
            detail: Raw server-provided error text.
        """
        super().__init__("NOT_FOUND", detail)


class TemporalAlreadyExistsError(_TemplatedRpcError):
    """Raised when Temporal reports ALREADY_EXISTS for the target resource."""

    _template = MSG_RPC_ALREADY_EXISTS

    def __init__(self, detail: str) -> None:
        """Initialize with the server detail.

        Args:
            detail: Raw server-provided error text.
        """
        super().__init__("ALREADY_EXISTS", detail)


class TemporalRateLimitedError(_TemplatedRpcError):
    """Raised when Temporal reports RESOURCE_EXHAUSTED (rate limit or quota)."""

    _template = MSG_RPC_RATE_LIMITED

    def __init__(self, detail: str) -> None:
        """Initialize with the server detail.

        Args:
            detail: Raw server-provided error text.
        """
        super().__init__("RESOURCE_EXHAUSTED", detail)


class TemporalInvalidRequestError(_TemplatedRpcError):
    """Raised when Temporal rejects the request (INVALID_ARGUMENT/FAILED_PRECONDITION/OUT_OF_RANGE)."""

    _template = MSG_RPC_INVALID


class TemporalPermissionDeniedError(_TemplatedRpcError):
    """Raised when Temporal denies access (PERMISSION_DENIED/UNAUTHENTICATED)."""

    _template = MSG_RPC_PERMISSION


class TemporalUnavailableError(_TemplatedRpcError):
    """Raised when the Temporal server is unreachable or too slow (UNAVAILABLE/DEADLINE_EXCEEDED)."""

    _template = MSG_RPC_UNAVAILABLE
