"""Tests for the batch-operations tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.batch_tools import temporal_batch_mcp


EXPECTED = {"list_batch_operations", "describe_batch_operation", "stop_batch_operation"}
READS = {"list_batch_operations", "describe_batch_operation"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_batch_mcp.list_tools())}


def test_batch_tools_registered():
    assert set(_tools()) == EXPECTED


def test_read_tools_are_read_only():
    for name in READS:
        tool = _tools()[name]
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.title
        assert TemporalToolTags.BATCH in tool.tags
        assert TemporalToolTags.READ in tool.tags


def test_stop_tool_is_mutating():
    tool = _tools()["stop_batch_operation"]
    assert tool.annotations.readOnlyHint is False
    assert tool.annotations.title
    assert TemporalToolTags.BATCH in tool.tags
    assert TemporalToolTags.MUTATING in tool.tags
