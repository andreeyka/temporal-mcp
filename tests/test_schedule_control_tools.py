"""Tests for the schedule-control tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.schedule_control_tools import temporal_schedule_control_mcp


EXPECTED = {"create_schedule", "update_schedule", "trigger_schedule", "backfill_schedule"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_schedule_control_mcp.list_tools())}


def test_schedule_control_tools_registered():
    assert set(_tools()) == EXPECTED


def test_schedule_control_tools_are_write():
    for tool in _tools().values():
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.title


def test_schedule_control_tools_tagged_mutating():
    for tool in _tools().values():
        assert TemporalToolTags.MUTATING in tool.tags
        assert TemporalToolTags.SCHEDULE in tool.tags
