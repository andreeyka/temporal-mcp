"""Tests for the worker-deployment tools provider."""

import asyncio

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.tools.worker_deployment_tools import temporal_worker_deployment_mcp


EXPECTED = {"list_worker_deployments", "describe_worker_deployment"}


def _tools():
    return {t.name: t for t in asyncio.run(temporal_worker_deployment_mcp.list_tools())}


def test_worker_deployment_tools_registered():
    assert set(_tools()) == EXPECTED


def test_worker_deployment_tools_are_read_only():
    for tool in _tools().values():
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.title
        assert TemporalToolTags.WORKER_DEPLOYMENT in tool.tags
        assert TemporalToolTags.READ in tool.tags
