"""Domain-specific exceptions."""

from __future__ import annotations

from temporal_mcp.errors.base import TemporalMcpError
from temporal_mcp.errors.messages import (
    MSG_AUTH_VERIFIER_REQUIRED,
    MSG_CONNECTION,
    MSG_CONNECTION_WITH_DETAIL,
    MSG_EXCHANGE,
    MSG_EXCHANGE_WITH_DETAIL,
    MSG_INCOMING_AUTH_CONFIG,
    MSG_SCHEDULE_SPEC_REQUIRED,
    MSG_UNKNOWN_STATUS,
)


class UnknownWorkflowStatusError(TemporalMcpError):
    """Raised when a status string is not a valid Temporal execution status."""

    def __init__(self, status: str, valid: list[str]) -> None:
        """Initialize with the bad status and the valid set.

        Args:
            status: The unrecognized status value.
            valid: Sorted list of accepted status names.
        """
        super().__init__(MSG_UNKNOWN_STATUS.format(status=status, valid=valid))
        self.status = status
        self.valid = valid


class TemporalAuthError(TemporalMcpError):
    """Raised when the caller identity/token cannot be resolved."""


class TemporalConnectionError(TemporalMcpError):
    """Raised when a Temporal client connection fails."""

    def __init__(self, host: str, *, detail: str | None = None) -> None:
        """Initialize with the target host and optional detail.

        Args:
            host: Temporal frontend address.
            detail: Optional underlying error text.
        """
        if detail:
            message = MSG_CONNECTION_WITH_DETAIL.format(host=host, detail=detail)
        else:
            message = MSG_CONNECTION.format(host=host)
        super().__init__(message)
        self.host = host


class TokenExchangeError(TemporalMcpError):
    """Raised when an RFC 8693 token exchange fails."""

    def __init__(self, *, detail: str | None = None) -> None:
        """Initialize with optional detail.

        Args:
            detail: Optional underlying error text.
        """
        message = MSG_EXCHANGE_WITH_DETAIL.format(detail=detail) if detail else MSG_EXCHANGE
        super().__init__(message)


class InvalidScheduleSpecError(TemporalMcpError):
    """Raised when a schedule is created/updated without a cron or interval spec."""

    def __init__(self) -> None:
        """Initialize with the fixed schedule-spec-required message."""
        super().__init__(MSG_SCHEDULE_SPEC_REQUIRED)


class MissingAuthVerifierError(TemporalMcpError):
    """Raised when passthrough/exchange auth is enabled without a token verifier."""

    def __init__(self, auth_mode: str) -> None:
        """Initialize with the auth mode that requires a verifier.

        Args:
            auth_mode: The outbound auth mode lacking incoming token verification.
        """
        super().__init__(MSG_AUTH_VERIFIER_REQUIRED.format(mode=auth_mode))
        self.auth_mode = auth_mode


class IncomingAuthConfigError(TemporalMcpError):
    """Raised when the selected incoming auth mode is missing a required variable."""

    def __init__(self, mode: str, missing: str) -> None:
        """Initialize with the auth mode and the missing configuration variable.

        Args:
            mode: The selected MCP_AUTH_MODE value.
            missing: Name of the required environment variable that is unset.
        """
        super().__init__(MSG_INCOMING_AUTH_CONFIG.format(mode=mode, missing=missing))
        self.mode = mode
        self.missing = missing
