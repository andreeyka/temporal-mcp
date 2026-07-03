"""Tests for the Nexus endpoint tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.nexus_tools import temporal_nexus_mcp


EXPECTED = {"list_nexus_endpoints", "get_nexus_endpoint", "create_nexus_endpoint", "delete_nexus_endpoint"}
READS = {"list_nexus_endpoints", "get_nexus_endpoint"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_nexus_mcp.list_tools())}


def test_nexus_tools_registered():
    assert set(_tools()) == EXPECTED


def test_read_tools_are_read_only_and_tagged():
    tools = _tools()
    for name in READS:
        tool = tools[name]
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.title
        assert TemporalToolTags.NEXUS in tool.tags
        assert TemporalToolTags.READ in tool.tags


def test_create_tool_is_write_and_tagged_mutating():
    tool = _tools()["create_nexus_endpoint"]
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is False
    assert tool.annotations.title
    assert TemporalToolTags.NEXUS in tool.tags
    assert TemporalToolTags.MUTATING in tool.tags


def test_delete_tool_is_mutating_and_destructive():
    tool = _tools()["delete_nexus_endpoint"]
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.destructiveHint is True
    assert tool.annotations.idempotentHint is False
    assert tool.annotations.title
    assert TemporalToolTags.NEXUS in tool.tags
    assert TemporalToolTags.MUTATING in tool.tags
