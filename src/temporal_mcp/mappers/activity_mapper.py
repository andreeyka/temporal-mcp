"""Mappers for activity execution SDK objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import enum_name, iso_datetime
from temporal_mcp.models import ActivityDetail, ActivitySummary


# Any is constrained to SDK mapper boundaries with dynamic attributes.


def activity_summary(raw: object) -> ActivitySummary:
    """Map an activity execution to an activity summary model."""
    execution = cast("Any", raw)
    return ActivitySummary(
        activity_id=execution.activity_id,
        activity_run_id=execution.activity_run_id,
        activity_type=execution.activity_type,
        status=enum_name(execution.status),
        task_queue=execution.task_queue,
        scheduled_time=iso_datetime(execution.scheduled_time),
        close_time=iso_datetime(execution.close_time),
    )


def activity_detail(raw: object) -> ActivityDetail:
    """Map an activity execution description to an activity detail model."""
    description = cast("Any", raw)
    summary = activity_summary(raw).model_dump()
    return ActivityDetail(
        **summary,
        attempt=description.attempt,
        run_state=enum_name(description.run_state),
        paused=description.paused,
        last_heartbeat_time=iso_datetime(description.last_heartbeat_time),
        last_failure=str(description.last_failure) if description.last_failure else None,
    )


def activity_summaries(raw: list[object]) -> list[ActivitySummary]:
    """Map activity executions to activity summary models."""
    return [activity_summary(execution) for execution in raw]
