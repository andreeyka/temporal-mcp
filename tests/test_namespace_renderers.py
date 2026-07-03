"""Tests for namespace renderers."""

from temporal_mcp.models import NamespaceDetail, NamespaceSummary
from temporal_mcp.renderers import namespace_renderer


def test_namespace_list_renders_table() -> None:
    text = namespace_renderer.namespace_list([NamespaceSummary(name="default", state="Registered")])

    assert "## Namespaces" in text
    assert "| name | state | description | retention_seconds |" in text
    assert "default" in text


def test_namespace_detail_renders_detail_block() -> None:
    text = namespace_renderer.namespace_detail(NamespaceDetail(name="default", state="Registered"))

    assert "## Namespace" in text
    assert "**name**" in text
    assert "default" in text
