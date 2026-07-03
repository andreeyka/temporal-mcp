"""Tests for read-only failure-analysis MCP tools."""

import asyncio
from types import SimpleNamespace

from temporal_mcp.models import WorkflowFailureAnalysis


def test_failure_tools_registered():
    from temporal_mcp.tools.failure_tools import temporal_failure_mcp

    names = {t.name for t in asyncio.run(temporal_failure_mcp.list_tools())}
    assert {"analyze_workflow_failure", "summarize_namespace_failures", "top_failure_types"} <= names


def test_failure_tools_are_read_only():
    from temporal_mcp.tools.failure_tools import temporal_failure_mcp

    for tool in asyncio.run(temporal_failure_mcp.list_tools()):
        assert tool.annotations.readOnlyHint is True
        assert "failure" in tool.tags


def test_since_pattern_rejects_bad_value():
    import pytest
    from pydantic import TypeAdapter, ValidationError

    from temporal_mcp.tools.failure_tools import Since

    ta = TypeAdapter(Since)
    ta.validate_python("2026-01-01T00:00:00Z")  # valid, no raise
    with pytest.raises(ValidationError):
        ta.validate_python("2026 OR 1=1")


def test_analyze_tool_maps_raw_service_data(monkeypatch):
    from temporal_mcp.tools import failure_tools

    service = SimpleNamespace(fetch_workflow_failure_data=_async_value(_workflow_data()))
    monkeypatch.setattr(failure_tools.failure_mapper, "build_analysis", _analysis_mapper)
    monkeypatch.setattr(failure_tools.failure_renderer, "failure_analysis", lambda _: "rendered")

    result = asyncio.run(
        failure_tools.analyze_workflow_failure("ns", "wf", structured_content=True, failure_service=service)
    )

    assert result.content[0].text == "rendered"
    assert result.structured_content["analysis"]["workflow_id"] == "wf"


def test_summary_tool_maps_raw_service_data(monkeypatch):
    from temporal_mcp.tools import failure_tools

    service = SimpleNamespace(fetch_namespace_failure_data=_async_value(_namespace_data()))
    monkeypatch.setattr(failure_tools.failure_mapper, "root_causes_of_histories", lambda _: [])
    monkeypatch.setattr(failure_tools.failure_renderer, "failure_summary", lambda _: "summary")

    result = asyncio.run(
        failure_tools.summarize_namespace_failures("ns", structured_content=True, failure_service=service)
    )

    assert result.content[0].text == "summary"
    assert result.structured_content["summary"]["total_failed"] == 3


def _workflow_data():
    return SimpleNamespace(namespace="ns", workflow_id="wf", run_id=None, description=object(), history=object())


def _namespace_data():
    count = SimpleNamespace(count=3, groups=[])
    return SimpleNamespace(namespace="ns", since=None, count=count, histories=[], sample_size=100)


def _analysis_mapper(namespace, workflow_id, run_id, desc, history):
    return WorkflowFailureAnalysis(namespace=namespace, workflow_id=workflow_id, run_id=run_id)


def _async_value(value):
    async def _inner(*args, **kwargs):
        return value

    return _inner
