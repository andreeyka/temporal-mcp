"""Public error API."""

from temporal_mcp.errors.base import TemporalMcpError, TemporalRpcError
from temporal_mcp.errors.exceptions import (
    IncomingAuthConfigError,
    IncomingAuthPolicyConfigError,
    IncomingAuthPolicyDeniedError,
    InvalidScheduleSpecError,
    MissingAuthVerifierError,
    TemporalAuthError,
    TemporalConnectionError,
    TokenExchangeError,
    UnknownWorkflowStatusError,
)
from temporal_mcp.errors.rpc_exceptions import (
    TemporalAlreadyExistsError,
    TemporalInvalidRequestError,
    TemporalNotFoundError,
    TemporalPermissionDeniedError,
    TemporalRateLimitedError,
    TemporalUnavailableError,
    UnsupportedServerFeatureError,
)


__all__ = [
    "IncomingAuthConfigError",
    "IncomingAuthPolicyConfigError",
    "IncomingAuthPolicyDeniedError",
    "InvalidScheduleSpecError",
    "MissingAuthVerifierError",
    "TemporalAlreadyExistsError",
    "TemporalAuthError",
    "TemporalConnectionError",
    "TemporalInvalidRequestError",
    "TemporalMcpError",
    "TemporalNotFoundError",
    "TemporalPermissionDeniedError",
    "TemporalRateLimitedError",
    "TemporalRpcError",
    "TemporalUnavailableError",
    "TokenExchangeError",
    "UnknownWorkflowStatusError",
    "UnsupportedServerFeatureError",
]
