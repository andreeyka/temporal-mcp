"""Shared assertions for per-domain tool wiring tests."""

from __future__ import annotations

import asyncio

from temporal_mcp.config import McpServerConfig
from temporal_mcp.main import build


def assert_reads_and_writes(reads: tuple[str, ...], writes: tuple[str, ...]) -> None:
    """Assert reads are reachable/visible and writes are gated by read-only mode.

    Args:
        reads: Read tool names expected in both full and read-only builds.
        writes: Write tool names expected only in the full build (hidden under read-only).
    """
    full = asyncio.run(build(McpServerConfig()))
    read_only = asyncio.run(build(McpServerConfig(read_only=True)))
    for name in reads:
        assert asyncio.run(full.get_tool(name)) is not None
        assert asyncio.run(read_only.get_tool(name)) is not None
    for name in writes:
        assert asyncio.run(full.get_tool(name)) is not None
        assert asyncio.run(read_only.get_tool(name)) is None
