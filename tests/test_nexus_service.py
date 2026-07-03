"""Tests for the Nexus endpoint service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.nexus_service import TemporalNexusService


def _svc(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalNexusService(pool), pool


def test_list_nexus_endpoints_builds_request_and_returns_list():
    resp = MagicMock()
    resp.endpoints = ["e0", "e1"]
    client = MagicMock()
    client.operator_service.list_nexus_endpoints = AsyncMock(return_value=resp)
    svc, pool = _svc(client)
    out = asyncio.run(svc.list_nexus_endpoints("ns", page_size=25, name="foo"))
    assert out == ["e0", "e1"]
    req = client.operator_service.list_nexus_endpoints.call_args.args[0]
    assert req.page_size == 25
    assert req.name == "foo"
    pool.get.assert_awaited_once_with("ns")


def test_get_nexus_endpoint_returns_endpoint():
    resp = MagicMock(endpoint="ENDPOINT")
    client = MagicMock()
    client.operator_service.get_nexus_endpoint = AsyncMock(return_value=resp)
    svc, pool = _svc(client)
    out = asyncio.run(svc.get_nexus_endpoint("ns", "ep-1"))
    assert out == "ENDPOINT"
    req = client.operator_service.get_nexus_endpoint.call_args.args[0]
    assert req.id == "ep-1"
    pool.get.assert_awaited_once_with("ns")


def test_create_nexus_endpoint_builds_worker_target_and_returns_endpoint():
    resp = MagicMock(endpoint="CREATED")
    client = MagicMock()
    client.operator_service.create_nexus_endpoint = AsyncMock(return_value=resp)
    svc, pool = _svc(client)
    out = asyncio.run(svc.create_nexus_endpoint("ns", "my-endpoint", "target-ns", "tq"))
    assert out == "CREATED"
    req = client.operator_service.create_nexus_endpoint.call_args.args[0]
    assert req.spec.name == "my-endpoint"
    assert req.spec.target.worker.namespace == "target-ns"
    assert req.spec.target.worker.task_queue == "tq"
    pool.get.assert_awaited_once_with("ns")


def test_delete_nexus_endpoint_sends_id_and_version():
    client = MagicMock()
    client.operator_service.delete_nexus_endpoint = AsyncMock(return_value=None)
    svc, pool = _svc(client)
    asyncio.run(svc.delete_nexus_endpoint("ns", "ep-1", 3))
    req = client.operator_service.delete_nexus_endpoint.call_args.args[0]
    assert req.id == "ep-1"
    assert req.version == 3
    pool.get.assert_awaited_once_with("ns")
