"""Pydantic models for batch operation results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class BatchOperationSummary(BaseModel):
    """Summary of a batch operation."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    job_id: Annotated[str, Field(description="Batch operation job ID.")]
    state: Annotated[str | None, Field(description="Batch operation state.")] = None
    start_time: Annotated[str | None, Field(description="ISO-8601 start time.")] = None
    close_time: Annotated[str | None, Field(description="ISO-8601 close time.")] = None


class BatchOperationDetail(BatchOperationSummary):
    """Detailed batch operation state."""

    operation_type: Annotated[str | None, Field(description="Batch operation type.")] = None
    total_operation_count: Annotated[int, Field(description="Total operation count.")] = 0
    complete_operation_count: Annotated[int, Field(description="Completed operation count.")] = 0
    failure_operation_count: Annotated[int, Field(description="Failed operation count.")] = 0
    identity: Annotated[str, Field(description="Identity that started the operation.")] = ""
    reason: Annotated[str, Field(description="Reason for the batch operation.")] = ""
