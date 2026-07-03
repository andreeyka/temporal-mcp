"""Mappers for schedule SDK objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import iso_datetime
from temporal_mcp.models import ScheduleDetail, ScheduleList, ScheduleSummary


# Any is constrained to SDK mapper boundaries with dynamic attributes.


def schedule_summary(raw: object) -> ScheduleSummary:
    """Map a schedule SDK object to a summary model.

    Args:
        raw: Schedule SDK object.

    Returns:
        The mapped schedule summary.
    """
    schedule = cast("Any", raw)
    return ScheduleSummary(id=schedule.id, workflow_type=getattr(schedule.info, "workflow_type", None))


def schedule_list(namespace: str, raw: list[object]) -> ScheduleList:
    """Map schedule SDK objects to a schedule list model.

    Args:
        namespace: Temporal namespace.
        raw: Schedule SDK objects.

    Returns:
        The mapped schedule list.
    """
    schedules = [schedule_summary(item) for item in raw]
    return ScheduleList(namespace=namespace, count=len(schedules), schedules=schedules)


def schedule_detail(schedule_id: str, raw: object) -> ScheduleDetail:
    """Map a schedule description SDK object to a detail model.

    Args:
        schedule_id: Schedule ID.
        raw: Schedule description SDK object.

    Returns:
        The mapped schedule detail.
    """
    description = cast("Any", raw)
    state = description.schedule.state
    return ScheduleDetail(
        id=schedule_id,
        note=state.note or "",
        paused=state.paused,
        next_action_times=_next_action_times(description.info.next_action_times),
    )


def _next_action_times(raw: list[object] | None) -> list[str]:
    times = [iso_datetime(item) for item in raw or []]
    return [item for item in times if item is not None]
