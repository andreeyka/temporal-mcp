"""Pydantic models for schedule results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ScheduleSummary(BaseModel):
    """Summary of a schedule."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: Annotated[str, Field(description="Schedule ID.")]
    workflow_type: Annotated[str | None, Field(description="Scheduled workflow type name.")] = None


class ScheduleList(BaseModel):
    """List of schedules in a namespace."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    namespace: Annotated[str, Field(description="Temporal namespace.")]
    count: Annotated[int, Field(description="Number of schedules returned.")]
    schedules: Annotated[list[ScheduleSummary], Field(description="Schedule summaries.")]


class ScheduleDetail(BaseModel):
    """Detailed schedule state."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: Annotated[str, Field(description="Schedule ID.")]
    note: Annotated[str, Field(description="Schedule note.")] = ""
    paused: Annotated[bool, Field(description="Whether the schedule is paused.")] = False
    next_action_times: Annotated[list[str], Field(default_factory=list, description="ISO-8601 next action times.")]
