"""Read-only mode hides and blocks mutating tools inside FastMCP."""

import asyncio

import pytest
from fastmcp.exceptions import NotFoundError

from temporal_mcp.config import McpServerConfig
from temporal_mcp.main import build


def test_read_only_hides_mutations():
    app = asyncio.run(build(McpServerConfig(read_only=True)))
    assert asyncio.run(app.get_tool("terminate_workflow")) is None
    assert asyncio.run(app.get_tool("delete_schedule")) is None
    # a read tool remains present
    assert asyncio.run(app.get_tool("list_workflows")) is not None


def test_read_only_blocks_mutation_calls():
    app = asyncio.run(build(McpServerConfig(read_only=True)))
    with pytest.raises(NotFoundError):
        asyncio.run(app.call_tool("terminate_workflow", {"namespace": "n", "workflow_id": "w"}))


def test_full_mode_keeps_mutations():
    app = asyncio.run(build(McpServerConfig(read_only=False)))
    assert asyncio.run(app.get_tool("terminate_workflow")) is not None
