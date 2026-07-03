"""Tests for workflow lifecycle-control service methods."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.workflow_service import TemporalWorkflowService


def _svc_with_client(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalWorkflowService(pool)


def test_pause_workflow_builds_request():
    client = MagicMock()
    client.workflow_service.pause_workflow_execution = AsyncMock()
    svc = _svc_with_client(client)
    asyncio.run(svc.pause_workflow("ns", "wf", reason="maint"))
    req = client.workflow_service.pause_workflow_execution.call_args.args[0]
    assert req.namespace == "ns"
    assert req.workflow_id == "wf"
    assert req.reason == "maint"
    assert req.request_id  # non-empty


def test_unpause_workflow_builds_request():
    client = MagicMock()
    client.workflow_service.unpause_workflow_execution = AsyncMock()
    svc = _svc_with_client(client)
    asyncio.run(svc.unpause_workflow("ns", "wf"))
    req = client.workflow_service.unpause_workflow_execution.call_args.args[0]
    assert req.namespace == "ns"
    assert req.workflow_id == "wf"


def test_signal_with_start_delegates():
    handle = MagicMock(id="wf", result_run_id="r1")
    client = MagicMock()
    client.start_workflow = AsyncMock(return_value=handle)
    svc = _svc_with_client(client)
    out = asyncio.run(svc.signal_with_start_workflow("ns", "Type", "tq", "wf", "sig", [1], [2]))
    assert out is handle
    kwargs = client.start_workflow.call_args.kwargs
    assert kwargs["id"] == "wf"
    assert kwargs["task_queue"] == "tq"
    assert kwargs["start_signal"] == "sig"
    assert kwargs["start_signal_args"] == [1]


def test_update_workflow_executes_update():
    handle = MagicMock()
    handle.execute_update = AsyncMock(return_value="RESULT")
    client = MagicMock()
    client.get_workflow_handle = MagicMock(return_value=handle)
    svc = _svc_with_client(client)
    out = asyncio.run(svc.update_workflow("ns", "wf", "doThing", [42]))
    assert out == "RESULT"
    assert handle.execute_update.call_args.args[0] == "doThing"
    assert handle.execute_update.call_args.kwargs["args"] == [42]


def test_reset_workflow_builds_request():
    resp = MagicMock(run_id="newrun")
    client = MagicMock()
    client.workflow_service.reset_workflow_execution = AsyncMock(return_value=resp)
    svc = _svc_with_client(client)
    out = asyncio.run(svc.reset_workflow("ns", "wf", event_id=7, reason="rr"))
    assert out.run_id == "newrun"
    req = client.workflow_service.reset_workflow_execution.call_args.args[0]
    assert req.namespace == "ns"
    assert req.workflow_execution.workflow_id == "wf"
    assert req.workflow_task_finish_event_id == 7
    assert req.reason == "rr"
