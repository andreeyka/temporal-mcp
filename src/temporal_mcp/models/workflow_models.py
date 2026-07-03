"""Pydantic models for workflow read results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class FailureInfo(BaseModel):
    """Failure details surfaced from a history event.

    Note: `message` and `stack_trace` are produced by application/worker code and
    may carry application-domain sensitive data (e.g. business identifiers, or
    user input echoed back by error handlers). Treat them accordingly when
    logging, storing, or forwarding this model.
    """

    model_config = ConfigDict(extra="ignore")

    message: Annotated[str, Field(description="Failure message.")]
    type: Annotated[str | None, Field(description="Failure/error type name, if any.")] = None
    stack_trace: Annotated[str | None, Field(description="Captured stack trace, if any.")] = None


class ExecutionSummary(BaseModel):
    """Summary of a workflow execution."""

    model_config = ConfigDict(extra="ignore")

    namespace: Annotated[str, Field(description="Namespace of the execution.")]
    workflow_id: Annotated[str, Field(description="Workflow ID.")]
    run_id: Annotated[str | None, Field(description="Run ID.")] = None
    workflow_type: Annotated[str | None, Field(description="Workflow type name.")] = None
    task_queue: Annotated[str | None, Field(description="Task queue the workflow runs on.")] = None
    status: Annotated[str | None, Field(description="Execution status.")] = None
    start_time: Annotated[str | None, Field(description="ISO-8601 start time.")] = None
    close_time: Annotated[str | None, Field(description="ISO-8601 close time.")] = None
    execution_time: Annotated[str | None, Field(description="ISO-8601 execution (first run) time.")] = None
    history_length: Annotated[int | None, Field(description="Number of events in the workflow history.")] = None
    parent_id: Annotated[str | None, Field(description="Parent workflow ID, if any.")] = None
    parent_run_id: Annotated[str | None, Field(description="Parent run ID, if any.")] = None
    root_id: Annotated[str | None, Field(description="Root workflow ID of the tree, if any.")] = None


class ExecutionDetail(ExecutionSummary):
    """Execution summary plus search attributes."""

    search_attributes: Annotated[
        dict[str, object], Field(description="Search attributes attached to the execution.")
    ] = Field(default_factory=dict)


class HistoryEventModel(BaseModel):
    """A single, compacted history event.

    Note: `payloads` carries decoded workflow/activity input or result data
    produced by application code. It may contain application-domain sensitive
    data (e.g. business identifiers, PII, or secrets). It is populated only when
    explicitly requested; treat it accordingly when logging, storing, or
    forwarding this model.
    """

    model_config = ConfigDict(extra="ignore")

    event_id: Annotated[int, Field(description="History event ID.")]
    event_time: Annotated[str | None, Field(description="ISO-8601 event time.")] = None
    event_type: Annotated[str, Field(description="History event type name.")]
    failure: Annotated[FailureInfo | None, Field(description="Failure details for this event, if any.")] = None
    reason: Annotated[
        str | None, Field(description="Reason associated with the event (e.g. cancellation/termination), if any.")
    ] = None
    activity_type: Annotated[str | None, Field(description="Activity type/name associated with the event, if any.")] = (
        None
    )
    activity_id: Annotated[str | None, Field(description="Activity ID associated with the event, if any.")] = None
    payloads: Annotated[
        list[str] | None,
        Field(description="Decoded event payloads (workflow/activity input or result), if requested."),
    ] = None
