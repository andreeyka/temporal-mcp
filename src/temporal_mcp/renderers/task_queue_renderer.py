"""Render task queue and search attribute output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from temporal_mcp.renderers import markdown as md


if TYPE_CHECKING:
    from temporal_mcp.models import SearchAttributesInfo, TaskQueueInfo


_POLLER_COLUMNS = ("identity", "last_access_time")


def task_queue(payload: TaskQueueInfo) -> str:
    """Render task queue poller information as Markdown.

    Args:
        payload: Task queue payload to render.

    Returns:
        The rendered Markdown sections.
    """
    pollers = [item.model_dump(mode="json") for item in payload.pollers]
    meta = {"namespace": payload.namespace, "task_queue": payload.task_queue}
    return md.sections([md.dict_block(meta, "Task Queue"), md.dict_table(pollers, "Pollers", columns=_POLLER_COLUMNS)])


def search_attributes(payload: SearchAttributesInfo) -> str:
    """Render search attributes as Markdown.

    Args:
        payload: Search attributes payload to render.

    Returns:
        The rendered Markdown sections.
    """
    return md.sections(
        [
            md.dict_block({"namespace": payload.namespace}, "Search Attributes"),
            _attribute_section("Custom", payload.custom),
            _attribute_section("System", payload.system),
        ]
    )


def _attribute_section(title: str, attrs: dict[str, str]) -> str:
    values = cast("dict[str, object]", dict(attrs))
    return md.sections([md.heading(title, 3), md.kv(values)])
