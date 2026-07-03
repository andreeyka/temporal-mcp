"""Pydantic models for task queue results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TaskQueuePoller(BaseModel):
    """Task queue poller information."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    identity: Annotated[str, Field(description="Poller identity.")]
    last_access_time: Annotated[str | None, Field(description="ISO-8601 last access time.")] = None


class TaskQueueInfo(BaseModel):
    """Task queue information."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    namespace: Annotated[str, Field(description="Temporal namespace.")]
    task_queue: Annotated[str, Field(description="Task queue name.")]
    pollers: Annotated[list[TaskQueuePoller], Field(description="Task queue pollers.")]


class SearchAttributesInfo(BaseModel):
    """Search attribute information for a namespace."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    namespace: Annotated[str, Field(description="Temporal namespace.")]
    custom: Annotated[dict[str, str], Field(description="Custom search attributes by name.")]
    system: Annotated[dict[str, str], Field(description="System search attributes by name.")]
