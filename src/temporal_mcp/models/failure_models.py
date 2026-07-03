"""Pydantic models for failure analysis."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class RootCause(BaseModel):
    """The originating failure extracted from a workflow's cause chain.

    Note: `message` and `stack_trace` are produced by application/worker code and
    may carry application-domain sensitive data (e.g. business identifiers, or
    user input echoed back by error handlers). Treat them accordingly when
    logging, storing, or forwarding this model.
    """

    model_config = ConfigDict(extra="ignore")

    message: Annotated[str, Field(description="Human-readable failure message.")]
    category: Annotated[str, Field(description="Failure category (e.g. application, timeout, activity, canceled).")]
    error_type: Annotated[str | None, Field(description="Application error type name, if any.")] = None
    source: Annotated[str | None, Field(description="Source of the failure (service/worker), if known.")] = None
    stack_trace: Annotated[str | None, Field(description="Captured stack trace, if any.")] = None


class CauseLink(BaseModel):
    """One node in a failure cause chain (outer to inner).

    Note: `message` is produced by application/worker code and may carry
    application-domain sensitive data (see `RootCause`).
    """

    model_config = ConfigDict(extra="ignore")

    message: Annotated[str, Field(description="Failure message for this link in the cause chain.")]
    category: Annotated[str, Field(description="Failure category for this link.")]
    error_type: Annotated[str | None, Field(description="Error type name for this link, if any.")] = None


class LastFailedActivity(BaseModel):
    """The last (innermost) activity failure found in the cause chain, outer to inner."""

    model_config = ConfigDict(extra="ignore")

    activity_type: Annotated[str | None, Field(description="Type name of the last failed activity.")] = None
    activity_id: Annotated[str | None, Field(description="ID of the last failed activity.")] = None
    retry_state: Annotated[str | None, Field(description="Retry state of the activity at failure.")] = None
    failure: Annotated[RootCause | None, Field(description="Root cause of the activity failure.")] = None


class WorkflowFailureAnalysis(BaseModel):
    """Root-cause analysis of a single workflow execution.

    Note: nested `root_cause`, `cause_chain`, and `last_failed_activity.failure`
    carry `message`/`stack_trace` text from application/worker code, which may
    include application-domain sensitive data (see `RootCause`).
    """

    model_config = ConfigDict(extra="ignore")

    namespace: Annotated[str, Field(description="Namespace of the analyzed workflow.")]
    workflow_id: Annotated[str, Field(description="ID of the analyzed workflow.")]
    run_id: Annotated[str | None, Field(description="Run ID of the analyzed execution.")] = None
    workflow_type: Annotated[str | None, Field(description="Workflow type name.")] = None
    status: Annotated[str | None, Field(description="Execution status (e.g. Failed, TimedOut, Terminated).")] = None
    close_time: Annotated[str | None, Field(description="ISO-8601 close time of the execution.")] = None
    root_cause: Annotated[RootCause | None, Field(description="Originating failure from the cause chain.")] = None
    cause_chain: Annotated[list[CauseLink], Field(description="Failure cause chain, outer to inner.")] = Field(
        default_factory=list
    )
    last_failed_activity: Annotated[
        LastFailedActivity | None, Field(description="Last activity failure found in the cause chain.")
    ] = None
    termination_reason: Annotated[
        str | None, Field(description="Reason the workflow was terminated, if applicable.")
    ] = None
    timeout_type: Annotated[str | None, Field(description="Timeout type, if the workflow timed out.")] = None


class FailureGroup(BaseModel):
    """A group of failures sharing a key (workflow type or error signature)."""

    model_config = ConfigDict(extra="ignore")

    key: Annotated[str, Field(description="Grouping key (workflow type or error signature).")]
    count: Annotated[int, Field(description="Number of failures in this group.")]
    sampled: Annotated[bool, Field(description="Whether the counts come from a sample, not an exact total.")] = False
    representative: Annotated[RootCause | None, Field(description="A representative root cause for the group.")] = None


class FailureSummary(BaseModel):
    """Namespace failure summary: exact totals plus sampled error-type breakdown."""

    model_config = ConfigDict(extra="ignore")

    namespace: Annotated[str, Field(description="Namespace summarized.")]
    since: Annotated[str | None, Field(description="Optional ISO-8601 lower bound on StartTime.")] = None
    total_failed: Annotated[int, Field(description="Exact total number of failed workflows.")] = 0
    by_workflow_type: Annotated[list[FailureGroup], Field(description="Failure groups keyed by workflow type.")] = (
        Field(default_factory=list)
    )
    by_error_type: Annotated[
        list[FailureGroup], Field(description="Failure groups keyed by error type (from the sample).")
    ] = Field(default_factory=list)
    sample_size: Annotated[int, Field(description="Failed workflows sampled for the error-type breakdown.")] = 0
    note: Annotated[str, Field(description="Optional note about the summary (e.g. sampling caveats).")] = ""
