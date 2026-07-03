"""Tests for the workflow-control tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.workflow_control_tools import temporal_workflow_control_mcp


EXPECTED = {"pause_workflow", "unpause_workflow", "signal_with_start_workflow", "update_workflow", "reset_workflow"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_workflow_control_mcp.list_tools())}


def test_control_tools_registered():
    assert set(_tools()) == EXPECTED


def test_control_tools_annotations():
    tools = _tools()
    for name in ("pause_workflow", "unpause_workflow", "signal_with_start_workflow", "update_workflow"):
        assert tools[name].annotations.readOnlyHint is False
        assert tools[name].annotations.destructiveHint is False
        assert tools[name].annotations.title
    assert tools["reset_workflow"].annotations.destructiveHint is True
    assert tools["reset_workflow"].annotations.title == "Reset Workflow"


def test_control_tools_tagged_mutating():
    for tool in _tools().values():
        assert TemporalToolTags.MUTATING in tool.tags
