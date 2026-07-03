"""Tests for the batch operations service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.batch_service import TemporalBatchService


def _svc(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalBatchService(pool)


def test_list_batch_operations_builds_request_and_returns_list():
    resp = MagicMock()
    resp.operation_info = ["op0", "op1"]
    client = MagicMock()
    client.workflow_service.list_batch_operations = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.list_batch_operations("ns", page_size=25))
    assert out == ["op0", "op1"]
    req = client.workflow_service.list_batch_operations.call_args.args[0]
    assert req.namespace == "ns"
    assert req.page_size == 25


def test_describe_batch_operation_returns_response():
    resp = MagicMock()
    client = MagicMock()
    client.workflow_service.describe_batch_operation = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.describe_batch_operation("ns", "job-1"))
    assert out is resp
    req = client.workflow_service.describe_batch_operation.call_args.args[0]
    assert req.namespace == "ns"
    assert req.job_id == "job-1"


def test_stop_batch_operation_builds_reason_and_identity():
    client = MagicMock()
    client.workflow_service.stop_batch_operation = AsyncMock(return_value=MagicMock())
    svc = _svc(client)
    out = asyncio.run(svc.stop_batch_operation("ns", "job-1", "reason", identity="me"))
    assert out is None
    req = client.workflow_service.stop_batch_operation.call_args.args[0]
    assert req.namespace == "ns"
    assert req.job_id == "job-1"
    assert req.reason == "reason"
    assert req.identity == "me"


def test_stop_batch_operation_defaults_identity():
    client = MagicMock()
    client.workflow_service.stop_batch_operation = AsyncMock(return_value=MagicMock())
    svc = _svc(client)
    asyncio.run(svc.stop_batch_operation("ns", "job-1", "reason"))
    req = client.workflow_service.stop_batch_operation.call_args.args[0]
    assert req.identity == "temporal-mcp"
