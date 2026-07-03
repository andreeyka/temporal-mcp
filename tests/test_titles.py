"""Every registered read tool exposes a human-readable title."""

import asyncio

from temporal_mcp.tools.failure_tools import temporal_failure_mcp
from temporal_mcp.tools.namespace_tools import temporal_namespace_mcp
from temporal_mcp.tools.schedule_tools import temporal_schedule_mcp
from temporal_mcp.tools.task_queue_tools import temporal_task_queue_mcp
from temporal_mcp.tools.workflow_mutate_tools import temporal_workflow_mutate_mcp
from temporal_mcp.tools.workflow_read_tools import temporal_workflow_read_mcp


EXPECTED_READ_TITLES = {
    "get_cluster_info": "Get Cluster Info",
    "list_namespaces": "List Namespaces",
    "describe_namespace": "Describe Namespace",
    "list_workflows": "List Workflows",
    "describe_workflow": "Describe Workflow",
    "get_workflow_history": "Get Workflow History",
    "count_workflows": "Count Workflows",
    "describe_task_queue": "Describe Task Queue",
    "list_search_attributes": "List Search Attributes",
    "analyze_workflow_failure": "Analyze Workflow Failure",
    "summarize_namespace_failures": "Summarize Namespace Failures",
    "top_failure_types": "Top Failure Types",
    "list_schedules": "List Schedules",
    "describe_schedule": "Describe Schedule",
}


def _titles(*providers):
    out = {}
    for provider in providers:
        for tool in asyncio.run(provider.list_tools()):
            out[tool.name] = tool.annotations.title if tool.annotations else None
    return out


def test_read_tools_have_expected_titles():
    titles = _titles(
        temporal_namespace_mcp,
        temporal_workflow_read_mcp,
        temporal_task_queue_mcp,
        temporal_failure_mcp,
        temporal_schedule_mcp,
    )
    for name, title in EXPECTED_READ_TITLES.items():
        assert titles.get(name) == title, f"{name}: {titles.get(name)!r}"


def test_read_tools_are_read_only():
    for provider in (
        temporal_namespace_mcp,
        temporal_workflow_read_mcp,
        temporal_task_queue_mcp,
        temporal_failure_mcp,
    ):
        for tool in asyncio.run(provider.list_tools()):
            assert tool.annotations.readOnlyHint is True


EXPECTED_WRITE = {
    "start_workflow",
    "signal_workflow",
    "query_workflow",
    "cancel_workflow",
    "pause_schedule",
    "unpause_schedule",
}
EXPECTED_DESTRUCTIVE = {"terminate_workflow", "delete_schedule"}


def test_mutating_tools_classification_and_titles():
    tools = {}
    for provider in (temporal_workflow_mutate_mcp, temporal_schedule_mcp):
        for tool in asyncio.run(provider.list_tools()):
            tools[tool.name] = tool.annotations
    for name in EXPECTED_WRITE:
        assert tools[name].readOnlyHint is False
        assert tools[name].destructiveHint is False, name
        assert tools[name].title
    for name in EXPECTED_DESTRUCTIVE:
        assert tools[name].destructiveHint is True, name
        assert tools[name].title
