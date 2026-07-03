"""Tests for the activity tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.activity_tools import temporal_activity_mcp


EXPECTED = {"list_activities", "describe_activity"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_activity_mcp.list_tools())}


def test_activity_tools_registered():
    assert set(_tools()) == EXPECTED


def test_activity_tools_are_read_only():
    for tool in _tools().values():
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.title
        assert TemporalToolTags.ACTIVITY in tool.tags
        assert TemporalToolTags.READ in tool.tags
