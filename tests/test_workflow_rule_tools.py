"""Tests for the workflow-rule tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.workflow_rule_tools import temporal_workflow_rule_mcp


EXPECTED = {"list_workflow_rules", "describe_workflow_rule", "create_workflow_rule", "delete_workflow_rule"}
READS = {"list_workflow_rules", "describe_workflow_rule"}
WRITES = {"create_workflow_rule"}
DESTRUCTIVE = {"delete_workflow_rule"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_workflow_rule_mcp.list_tools())}


def test_workflow_rule_tools_registered():
    assert set(_tools()) == EXPECTED


def test_read_tools_are_read_only():
    tools = _tools()
    for name in READS:
        tool = tools[name]
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.title
        assert TemporalToolTags.WORKFLOW_RULE in tool.tags
        assert TemporalToolTags.READ in tool.tags


def test_create_tool_is_write():
    tool = _tools()["create_workflow_rule"]
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.title
    assert TemporalToolTags.WORKFLOW_RULE in tool.tags
    assert TemporalToolTags.MUTATING in tool.tags


def test_delete_tool_is_destructive():
    tool = _tools()["delete_workflow_rule"]
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is True
    assert tool.annotations.idempotentHint is False
    assert tool.annotations.title
    assert TemporalToolTags.WORKFLOW_RULE in tool.tags
    assert TemporalToolTags.MUTATING in tool.tags
