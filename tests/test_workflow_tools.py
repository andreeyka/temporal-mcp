import asyncio

from temporal_mcp.tools.workflow_mutate_tools import temporal_workflow_mutate_mcp
from temporal_mcp.tools.workflow_read_tools import temporal_workflow_read_mcp


def test_read_provider_has_4_tools():
    names = sorted(t.name for t in asyncio.run(temporal_workflow_read_mcp.list_tools()))
    assert names == ["count_workflows", "describe_workflow", "get_workflow_history", "list_workflows"]


def test_mutate_provider_has_5_tools():
    names = sorted(t.name for t in asyncio.run(temporal_workflow_mutate_mcp.list_tools()))
    assert names == ["cancel_workflow", "query_workflow", "signal_workflow", "start_workflow", "terminate_workflow"]
