"""Render Nexus endpoint output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import NexusEndpointDetail, NexusEndpointSummary


_ENTITY_RENDERER = EntityRenderer()
_NEXUS_ENDPOINT_COLUMNS = ("id", "name", "url_prefix", "version", "created_time")
_NEXUS_ENDPOINT_SPEC = RenderSpec(title="Nexus Endpoints", columns=_NEXUS_ENDPOINT_COLUMNS)


def nexus_endpoint_list(items: list[NexusEndpointSummary]) -> str:
    """Render Nexus endpoint summaries as Markdown.

    Args:
        items: Nexus endpoint summaries to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.list(items, _NEXUS_ENDPOINT_SPEC)


def nexus_endpoint_detail(detail: NexusEndpointDetail) -> str:
    """Render one Nexus endpoint as Markdown.

    Args:
        detail: Nexus endpoint detail to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.detail(detail, "Nexus Endpoint")
