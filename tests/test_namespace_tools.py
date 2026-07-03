# tests/test_namespace_tools.py
from temporal_mcp.tools.namespace_tools import temporal_namespace_mcp


def test_namespace_provider_exists():
    assert temporal_namespace_mcp is not None
