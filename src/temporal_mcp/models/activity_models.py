"""Pydantic models for activity results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ActivitySummary(BaseModel):
    """Summary of an activity execution."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    activity_id: Annotated[str, Field(description="Activity ID.")]
    activity_run_id: Annotated[str | None, Field(description="Activity run ID.")] = None
    activity_type: Annotated[str | None, Field(description="Activity type name.")] = None
    status: Annotated[str | None, Field(description="Activity status.")] = None
    task_queue: Annotated[str | None, Field(description="Task queue name.")] = None
    scheduled_time: Annotated[str | None, Field(description="ISO-8601 scheduled time.")] = None
    close_time: Annotated[str | None, Field(description="ISO-8601 close time.")] = None


class ActivityDetail(ActivitySummary):
    """Detailed activity execution state."""

    attempt: Annotated[int | None, Field(description="Current activity attempt number.")] = None
    run_state: Annotated[str | None, Field(description="Current activity run state.")] = None
    paused: Annotated[bool | None, Field(description="Whether the activity is paused.")] = None
    last_heartbeat_time: Annotated[str | None, Field(description="ISO-8601 last heartbeat time.")] = None
    last_failure: Annotated[str | None, Field(description="Last activity failure text, if any.")] = None
