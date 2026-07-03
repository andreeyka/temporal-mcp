"""Unit tests for the Temporal MCP resources (direct call with mocked services)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import temporal_mcp.resources.resources as res
from temporal_mcp.models.namespace_models import NamespaceSummary


def _namespace_service(summaries):
    resp = MagicMock()
    resp.namespaces = summaries
    svc = MagicMock()
    svc.list_namespaces = AsyncMock(return_value=resp)
    return svc


def test_namespaces_resource_lists_namespaces(monkeypatch):
    # The resource maps namespace_mapper.namespace_summary over resp.namespaces;
    # stub it to identity so this test exercises resource JSON rendering.
    monkeypatch.setattr(res.namespace_mapper, "namespace_summary", lambda n: n)
    svc = _namespace_service(
        [NamespaceSummary(name="a", state="Registered"), NamespaceSummary(name="b", state="Deprecated")]
    )
    data = json.loads(asyncio.run(res.namespaces_resource(namespace_service=svc)))
    assert [d["name"] for d in data] == ["a", "b"]
    svc.list_namespaces.assert_awaited_once()


def test_namespace_failures_resource_returns_summary_json():
    svc = MagicMock()
    svc.fetch_namespace_failure_data = AsyncMock(
        return_value=SimpleNamespace(
            namespace="prod",
            since=None,
            count=SimpleNamespace(count=3, groups=[]),
            histories=[],
            sample_size=100,
        )
    )
    text = asyncio.run(res.namespace_failures_resource("prod", failure_service=svc))
    data = json.loads(text)
    assert data["namespace"] == "prod"
    assert data["total_failed"] == 3
    svc.fetch_namespace_failure_data.assert_awaited_once_with("prod")
