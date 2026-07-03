"""Pydantic models for worker deployment results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class WorkerDeploymentSummary(BaseModel):
    """Summary of a worker deployment."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    name: Annotated[str, Field(description="Worker deployment name.")]
    create_time: Annotated[str | None, Field(description="ISO-8601 create time.")] = None


class WorkerDeploymentDetail(WorkerDeploymentSummary):
    """Detailed worker deployment state."""

    last_modifier_identity: Annotated[str, Field(description="Identity that last modified the deployment.")] = ""
    manager_identity: Annotated[str, Field(description="Worker deployment manager identity.")] = ""
    version_count: Annotated[int, Field(description="Number of worker deployment versions.")] = 0
