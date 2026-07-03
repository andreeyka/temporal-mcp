"""Tests for the worker-deployment service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.worker_deployment_service import TemporalWorkerDeploymentService


def _svc(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalWorkerDeploymentService(pool)


def test_list_worker_deployments_builds_request_and_returns_list():
    resp = MagicMock()
    resp.worker_deployments = ["d0", "d1", "d2"]
    client = MagicMock()
    client.workflow_service.list_worker_deployments = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.list_worker_deployments("ns", page_size=25))
    assert out == ["d0", "d1", "d2"]
    req = client.workflow_service.list_worker_deployments.call_args.args[0]
    assert req.namespace == "ns"
    assert req.page_size == 25


def test_describe_worker_deployment_returns_info():
    resp = MagicMock(worker_deployment_info="INFO")
    client = MagicMock()
    client.workflow_service.describe_worker_deployment = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.describe_worker_deployment("ns", "my-deploy"))
    assert out == "INFO"
    req = client.workflow_service.describe_worker_deployment.call_args.args[0]
    assert req.namespace == "ns"
    assert req.deployment_name == "my-deploy"
