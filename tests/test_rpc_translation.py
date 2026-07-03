"""Tests for gRPC status → registry exception translation."""

import pytest
from temporalio.service import RPCError, RPCStatusCode

from temporal_mcp.errors import (
    TemporalAlreadyExistsError,
    TemporalInvalidRequestError,
    TemporalNotFoundError,
    TemporalPermissionDeniedError,
    TemporalRateLimitedError,
    TemporalUnavailableError,
    UnsupportedServerFeatureError,
)
from temporal_mcp.errors.rpc_translation import find_rpc_error, translate_rpc_error


def _rpc(message: str, status: RPCStatusCode) -> RPCError:
    return RPCError(message, status, b"")


@pytest.mark.parametrize(
    ("status", "expected_type"),
    [
        (RPCStatusCode.NOT_FOUND, TemporalNotFoundError),
        (RPCStatusCode.ALREADY_EXISTS, TemporalAlreadyExistsError),
        (RPCStatusCode.INVALID_ARGUMENT, TemporalInvalidRequestError),
        (RPCStatusCode.FAILED_PRECONDITION, TemporalInvalidRequestError),
        (RPCStatusCode.OUT_OF_RANGE, TemporalInvalidRequestError),
        (RPCStatusCode.PERMISSION_DENIED, TemporalPermissionDeniedError),
        (RPCStatusCode.UNAUTHENTICATED, TemporalPermissionDeniedError),
        (RPCStatusCode.RESOURCE_EXHAUSTED, TemporalRateLimitedError),
        (RPCStatusCode.UNAVAILABLE, TemporalUnavailableError),
        (RPCStatusCode.DEADLINE_EXCEEDED, TemporalUnavailableError),
    ],
)
def test_translate_maps_actionable_statuses(status, expected_type):
    domain = translate_rpc_error(_rpc("server detail", status))
    assert isinstance(domain, expected_type)
    assert "server detail" in str(domain)
    assert domain.status_name == status.name


@pytest.mark.parametrize(
    "status",
    [
        RPCStatusCode.INTERNAL,
        RPCStatusCode.UNKNOWN,
        RPCStatusCode.DATA_LOSS,
        RPCStatusCode.ABORTED,
        RPCStatusCode.CANCELLED,
    ],
)
def test_translate_leaves_internal_statuses_unmapped(status):
    assert translate_rpc_error(_rpc("secret backend detail", status)) is None


def test_unimplemented_gets_standalone_activities_hint():
    msg = "unknown method ListActivityExecutions for service temporal.api.workflowservice.v1.WorkflowService"
    domain = translate_rpc_error(_rpc(msg, RPCStatusCode.UNIMPLEMENTED))
    assert isinstance(domain, UnsupportedServerFeatureError)
    assert "1.31.0" in str(domain)
    assert msg in str(domain)


def test_unimplemented_unknown_method_gets_generic_upgrade_hint():
    domain = translate_rpc_error(_rpc("unknown method SomeFutureRpc", RPCStatusCode.UNIMPLEMENTED))
    assert isinstance(domain, UnsupportedServerFeatureError)
    assert "1.31.0" not in str(domain)
    assert "newer version" in str(domain)


def test_find_rpc_error_direct_and_nested():
    rpc = _rpc("x", RPCStatusCode.NOT_FOUND)
    assert find_rpc_error(rpc) is rpc
    wrapped = RuntimeError("wrap")
    wrapped.__cause__ = rpc
    assert find_rpc_error(wrapped) is rpc
    outer = RuntimeError("outer")
    outer.__cause__ = wrapped
    assert find_rpc_error(outer) is rpc


def _raise_wrapper(rpc: RPCError, wrapper: BaseException, *, suppress: bool) -> None:
    try:
        raise rpc
    except RPCError:
        if suppress:
            raise wrapper from None
        raise wrapper  # noqa: B904 — deliberate: reproduce temporalio's implicit chaining


def test_find_rpc_error_follows_implicit_context():
    rpc = _rpc("already exists", RPCStatusCode.ALREADY_EXISTS)
    with pytest.raises(RuntimeError) as exc_info:
        _raise_wrapper(rpc, RuntimeError("temporalio-style wrapper without 'from'"), suppress=False)
    assert exc_info.value.__cause__ is None
    assert find_rpc_error(exc_info.value) is rpc


def test_find_rpc_error_absent_and_suppressed_context_ignored():
    assert find_rpc_error(RuntimeError("plain")) is None
    rpc = _rpc("suppressed", RPCStatusCode.NOT_FOUND)
    with pytest.raises(RuntimeError) as exc_info:
        _raise_wrapper(rpc, RuntimeError("explicitly suppressed chain"), suppress=True)
    assert find_rpc_error(exc_info.value) is None
