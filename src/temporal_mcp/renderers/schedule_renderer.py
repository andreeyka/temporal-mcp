"""Render schedule output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers import markdown as md
from temporal_mcp.renderers.entity_renderer import EntityRenderer


if TYPE_CHECKING:
    from temporal_mcp.models import ScheduleDetail, ScheduleList


_ENTITY_RENDERER = EntityRenderer()
_SCHEDULE_COLUMNS = ("id", "workflow_type")


def schedule_list(payload: ScheduleList) -> str:
    """Render a schedule list as Markdown.

    Args:
        payload: Schedule list payload to render.

    Returns:
        The rendered Markdown sections.
    """
    items = [item.model_dump(mode="json") for item in payload.schedules]
    meta = {"namespace": payload.namespace, "count": payload.count}
    return md.sections([md.dict_block(meta, "Schedules"), md.dict_table(items, "Items", columns=_SCHEDULE_COLUMNS)])


def schedule_detail(detail: ScheduleDetail) -> str:
    """Render one schedule detail as Markdown.

    Args:
        detail: Schedule detail to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.detail(detail, "Schedule")
