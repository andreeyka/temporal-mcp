"""Tests for the RPC error translation middleware."""

import asyncio
from types import SimpleNamespace

import pytest
from fastmcp.exceptions import ToolError
from temporalio.service import RPCError, RPCStatusCode

from temporal_mcp.errors import TemporalAlreadyExistsError, TemporalNotFoundError, UnsupportedServerFeatureError
from temporal_mcp.middleware import TemporalRpcErrorMiddleware


def _context(tool_name: str = "list_activities"):
    return SimpleNamespace(message=SimpleNamespace(name=tool_name))


def _call(middleware, call_next, tool_name: str = "list_activities"):
    return asyncio.run(middleware.on_call_tool(_context(tool_name), call_next))


def _raising(exc: BaseException):
    async def call_next(_context):
        raise exc

    return call_next


def test_translates_masked_toolerror_wrapping_rpc_error():
    rpc = RPCError(
        "unknown method ListActivityExecutions for service temporal.api.workflowservice.v1.WorkflowService",
        RPCStatusCode.UNIMPLEMENTED,
        b"",
    )
    masked = ToolError("Error calling tool 'list_activities'")
    masked.__cause__ = rpc
    with pytest.raises(UnsupportedServerFeatureError) as exc_info:
        _call(TemporalRpcErrorMiddleware(), _raising(masked))
    assert "1.31.0" in str(exc_info.value)


def test_translates_direct_rpc_error():
    rpc = RPCError("workflow not found", RPCStatusCode.NOT_FOUND, b"")
    with pytest.raises(TemporalNotFoundError):
        _call(TemporalRpcErrorMiddleware(), _raising(rpc))


def test_domain_errors_pass_through_unchanged():
    from temporal_mcp.errors import TemporalAuthError

    original = TemporalAuthError("no token")
    with pytest.raises(TemporalAuthError) as exc_info:
        _call(TemporalRpcErrorMiddleware(), _raising(original))
    assert exc_info.value is original


def test_non_rpc_errors_pass_through_unchanged():
    original = ToolError("Error calling tool 'x'")
    original.__cause__ = ValueError("plain bug")
    with pytest.raises(ToolError) as exc_info:
        _call(TemporalRpcErrorMiddleware(), _raising(original))
    assert exc_info.value is original


def test_unmapped_rpc_statuses_pass_through_unchanged():
    masked = ToolError("Error calling tool 'x'")
    masked.__cause__ = RPCError("backend exploded", RPCStatusCode.INTERNAL, b"")
    with pytest.raises(ToolError) as exc_info:
        _call(TemporalRpcErrorMiddleware(), _raising(masked))
    assert exc_info.value is masked


def test_successful_calls_return_result():
    async def call_next(_context):
        return "ok"

    assert _call(TemporalRpcErrorMiddleware(), call_next) == "ok"


def test_translates_temporalio_wrapper_left_in_context_chain():
    # temporalio's high-level client raises wrapper errors inside `except
    # RPCError:` without `from`, so the RPCError lives only in __context__.
    from temporalio.exceptions import WorkflowAlreadyStartedError

    def raise_wrapper_without_from(rpc: RPCError) -> None:
        try:
            raise rpc
        except RPCError:
            raise WorkflowAlreadyStartedError("wf-1", "MyWorkflow")  # noqa: B904 — reproduce SDK chaining

    rpc = RPCError("workflow execution already started", RPCStatusCode.ALREADY_EXISTS, b"")
    with pytest.raises(WorkflowAlreadyStartedError) as wrapper_info:
        raise_wrapper_without_from(rpc)
    masked = ToolError("Error calling tool 'start_workflow'")
    masked.__cause__ = wrapper_info.value
    with pytest.raises(TemporalAlreadyExistsError):
        _call(TemporalRpcErrorMiddleware(), _raising(masked))


def test_e2e_masked_server_translates_unimplemented_and_masks_internal():
    # Pins the fastmcp contract the middleware depends on: tool exceptions are
    # wrapped (masked) with the original kept in __cause__, and middleware runs
    # outside that wrap.
    from fastmcp import Client, FastMCP

    app = FastMCP(name="e2e", mask_error_details=True, middleware=[TemporalRpcErrorMiddleware()])

    @app.tool
    async def unimplemented_tool() -> str:
        raise RPCError(
            "unknown method ListActivityExecutions for service temporal.api.workflowservice.v1.WorkflowService",
            RPCStatusCode.UNIMPLEMENTED,
            b"",
        )

    @app.tool
    async def internal_tool() -> str:
        raise RPCError("secret backend detail", RPCStatusCode.INTERNAL, b"")

    async def scenario():
        async with Client(app) as client:
            unimplemented = await client.call_tool("unimplemented_tool", raise_on_error=False)
            internal = await client.call_tool("internal_tool", raise_on_error=False)
            return unimplemented, internal

    unimplemented, internal = asyncio.run(scenario())
    assert unimplemented.is_error
    assert "1.31.0" in unimplemented.content[0].text
    assert internal.is_error
    assert "secret backend detail" not in internal.content[0].text
