"""Render namespace output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import NamespaceDetail, NamespaceSummary


_ENTITY_RENDERER = EntityRenderer()
_NAMESPACE_COLUMNS = ("name", "state", "description", "retention_seconds")
_NAMESPACE_SPEC = RenderSpec(title="Namespaces", columns=_NAMESPACE_COLUMNS)


def namespace_list(items: list[NamespaceSummary]) -> str:
    """Render namespace summaries as Markdown."""
    return _ENTITY_RENDERER.list(items, _NAMESPACE_SPEC)


def namespace_detail(detail: NamespaceDetail) -> str:
    """Render one namespace as Markdown."""
    return _ENTITY_RENDERER.detail(detail, "Namespace")
