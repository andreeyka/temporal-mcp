"""Translate temporalio RPC errors into registry exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporalio.service import RPCError, RPCStatusCode

from temporal_mcp.errors.messages import MSG_HINT_STANDALONE_ACTIVITIES, MSG_HINT_UPGRADE
from temporal_mcp.errors.rpc_exceptions import (
    TemporalAlreadyExistsError,
    TemporalInvalidRequestError,
    TemporalNotFoundError,
    TemporalPermissionDeniedError,
    TemporalRateLimitedError,
    TemporalUnavailableError,
    UnsupportedServerFeatureError,
)


if TYPE_CHECKING:
    from collections.abc import Callable

    from temporal_mcp.errors.base import TemporalRpcError

_FEATURE_HINTS: dict[str, str] = {
    "ListActivityExecutions": MSG_HINT_STANDALONE_ACTIVITIES,
    "DescribeActivityExecution": MSG_HINT_STANDALONE_ACTIVITIES,
}
_TRANSLATORS: dict[RPCStatusCode, Callable[[RPCError], TemporalRpcError]] = {
    RPCStatusCode.NOT_FOUND: lambda e: TemporalNotFoundError(e.message),
    RPCStatusCode.ALREADY_EXISTS: lambda e: TemporalAlreadyExistsError(e.message),
    RPCStatusCode.RESOURCE_EXHAUSTED: lambda e: TemporalRateLimitedError(e.message),
    RPCStatusCode.INVALID_ARGUMENT: lambda e: TemporalInvalidRequestError(e.status.name, e.message),
    RPCStatusCode.FAILED_PRECONDITION: lambda e: TemporalInvalidRequestError(e.status.name, e.message),
    RPCStatusCode.OUT_OF_RANGE: lambda e: TemporalInvalidRequestError(e.status.name, e.message),
    RPCStatusCode.PERMISSION_DENIED: lambda e: TemporalPermissionDeniedError(e.status.name, e.message),
    RPCStatusCode.UNAUTHENTICATED: lambda e: TemporalPermissionDeniedError(e.status.name, e.message),
    RPCStatusCode.UNAVAILABLE: lambda e: TemporalUnavailableError(e.status.name, e.message),
    RPCStatusCode.DEADLINE_EXCEEDED: lambda e: TemporalUnavailableError(e.status.name, e.message),
}
_MAX_CAUSE_DEPTH = 10


def _chained(err: BaseException) -> BaseException | None:
    """Return the chained exception Python would report for the error.

    Explicit causes win; implicit context is followed unless suppressed via
    ``raise ... from None``.

    Args:
        err: The exception whose chain link to resolve.

    Returns:
        The next exception in the chain, or None.
    """
    if err.__cause__ is not None:
        return err.__cause__
    if not err.__suppress_context__:
        return err.__context__
    return None


def find_rpc_error(err: BaseException) -> RPCError | None:
    """Return the first RPCError in the exception's chain, if any.

    Both explicit causes (``raise ... from err``) and implicit context are
    followed — temporalio wraps RPCError without ``from``, leaving it only in
    ``__context__`` — while explicitly suppressed context is ignored.

    Args:
        err: The caught exception.

    Returns:
        The underlying RPCError, or None when the chain has none.
    """
    current: BaseException | None = err
    for _ in range(_MAX_CAUSE_DEPTH):
        if current is None:
            return None
        if isinstance(current, RPCError):
            return current
        current = _chained(current)
    return None


def _unimplemented_hint(detail: str) -> str:
    """Return the feature hint matching the failed RPC method name.

    Args:
        detail: Raw server-provided error text.

    Returns:
        A known feature/version hint, or the generic upgrade hint.
    """
    for method, hint in _FEATURE_HINTS.items():
        if method in detail:
            return hint
    return MSG_HINT_UPGRADE


def translate_rpc_error(err: RPCError) -> TemporalRpcError | None:
    """Map an RPCError to a registry exception when the status is client-actionable.

    Args:
        err: The RPC error from temporalio.

    Returns:
        A registry exception ready to raise, or None for statuses that must
        stay masked (internal server faults).
    """
    if err.status == RPCStatusCode.UNIMPLEMENTED:
        return UnsupportedServerFeatureError(err.message, hint=_unimplemented_hint(err.message))
    translator = _TRANSLATORS.get(err.status)
    return translator(err) if translator is not None else None
