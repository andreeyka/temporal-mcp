"""Render activity output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import ActivityDetail, ActivitySummary


_ENTITY_RENDERER = EntityRenderer()
_ACTIVITY_COLUMNS = (
    "activity_id",
    "activity_run_id",
    "activity_type",
    "status",
    "task_queue",
    "scheduled_time",
    "close_time",
)
_ACTIVITY_SPEC = RenderSpec(title="Activities", columns=_ACTIVITY_COLUMNS)


def activity_list(items: list[ActivitySummary]) -> str:
    """Render activity summaries as Markdown.

    Args:
        items: Activity summaries to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.list(items, _ACTIVITY_SPEC)


def activity_detail(detail: ActivityDetail) -> str:
    """Render one activity execution as Markdown.

    Args:
        detail: Activity detail to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.detail(detail, "Activity")
