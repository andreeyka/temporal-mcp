"""Build failure-analysis models from Temporal history and failure objects."""

from __future__ import annotations

from typing import Any

from temporalio.api.enums.v1 import RetryState, TimeoutType

from temporal_mcp.models import (
    CauseLink,
    FailureGroup,
    FailureSummary,
    LastFailedActivity,
    RootCause,
    WorkflowFailureAnalysis,
)


# Any is constrained to Temporal SDK/protobuf mapper boundaries with dynamic attributes.
_SIMPLE_CATEGORY = {
    "terminated_failure_info": "TerminatedFailure",
    "canceled_failure_info": "CanceledFailure",
    "server_failure_info": "ServerFailure",
    "activity_failure_info": "ActivityFailure",
    "child_workflow_execution_failure_info": "ChildWorkflowFailure",
    "reset_workflow_failure_info": "ResetWorkflowFailure",
    "nexus_operation_execution_failure_info": "NexusOperationFailure",
    "nexus_handler_failure_info": "NexusHandlerFailure",
}
_TERMINAL_ATTRS = (
    "workflow_execution_failed_event_attributes",
    "workflow_execution_terminated_event_attributes",
    "workflow_execution_timed_out_event_attributes",
    "workflow_execution_canceled_event_attributes",
)


def root_cause_of_history(history: object) -> RootCause | None:
    """Return the innermost RootCause from a history's terminal failure, or None."""
    terminal = _terminal_event(history)
    if terminal is None or terminal[0] != "workflow_execution_failed_event_attributes":
        return None
    return _root_cause(_chain(terminal[1].failure)[-1])


def root_causes_of_histories(histories: list[object]) -> list[RootCause]:
    """Return root causes extracted from raw histories."""
    causes = [root_cause_of_history(history) for history in histories]
    return [cause for cause in causes if cause is not None]


def build_analysis(
    namespace: str,
    workflow_id: str,
    run_id: str | None,
    desc: object,
    history: object,
) -> WorkflowFailureAnalysis:
    """Build a WorkflowFailureAnalysis from a describe result and history."""
    analysis = WorkflowFailureAnalysis(
        namespace=namespace,
        workflow_id=workflow_id,
        run_id=run_id or getattr(desc, "run_id", None),
        workflow_type=getattr(desc, "workflow_type", None),
        status=_status_name(desc),
        close_time=_iso(getattr(desc, "close_time", None)),
    )
    terminal = _terminal_event(history)
    return analysis if terminal is None else _apply_terminal(analysis, terminal)


def build_summary(
    namespace: str,
    since: str | None,
    count: object,
    causes: list[RootCause],
    sample_size: int,
) -> FailureSummary:
    """Build a FailureSummary from exact counts and a sampled cause list."""
    groups = getattr(count, "groups", [])
    by_type = [FailureGroup(key=_group_key(group), count=getattr(group, "count", 0)) for group in groups]
    return FailureSummary(
        namespace=namespace,
        since=since,
        total_failed=getattr(count, "count", 0),
        by_workflow_type=by_type,
        by_error_type=_aggregate(causes),
        sample_size=sample_size,
        note="by_error_type is derived from a bounded sample of failed workflow histories.",
    )


def top_groups(causes: list[RootCause], limit: int) -> list[FailureGroup]:
    """Return the top-`limit` error-signature groups by count."""
    return _aggregate(causes)[:limit]


def _enum_name(enum_cls: Any, value: int, prefix: str) -> str | None:  # noqa: ANN401
    """Return a stripped enum name (without prefix), or None for the zero value."""
    if not value:
        return None
    return enum_cls.Name(value).removeprefix(prefix)


def _categorize(failure: Any) -> tuple[str, str | None]:  # noqa: ANN401
    """Return (category, error_type) for a Failure via its failure_info oneof."""
    which = failure.WhichOneof("failure_info")
    if which is None:
        return "Failure", None
    if which == "application_failure_info":
        return "ApplicationFailure", failure.application_failure_info.type or None
    if which == "timeout_failure_info":
        name = _enum_name(TimeoutType, failure.timeout_failure_info.timeout_type, "TIMEOUT_TYPE_")
        return (f"TimeoutFailure:{name}" if name else "TimeoutFailure"), None
    return _SIMPLE_CATEGORY.get(which, "Failure"), None


def _root_cause(failure: Any) -> RootCause:  # noqa: ANN401
    """Build a RootCause from a single Failure object."""
    category, error_type = _categorize(failure)
    return RootCause(
        message=failure.message,
        category=category,
        error_type=error_type,
        source=failure.source or None,
        stack_trace=failure.stack_trace or None,
    )


def _chain(failure: Any) -> list[Any]:  # noqa: ANN401
    """Return failure objects from outer to inner, following `cause`."""
    out: list[Any] = []
    current = failure
    while current is not None:
        out.append(current)
        current = current.cause if current.HasField("cause") else None
    return out


def _cause_links(failure: Any) -> list[CauseLink]:  # noqa: ANN401
    """Return the cause chain as compact CauseLink nodes (outer to inner)."""
    links: list[CauseLink] = []
    for link in _chain(failure):
        category, error_type = _categorize(link)
        links.append(CauseLink(message=link.message, category=category, error_type=error_type))
    return links


def _signature(root_cause: RootCause) -> str:
    """Return a grouping signature: category|error_type|first message line."""
    first_line = root_cause.message.splitlines()[0] if root_cause.message else ""
    return f"{root_cause.category}|{root_cause.error_type or ''}|{first_line}"


def _aggregate(causes: list[RootCause]) -> list[FailureGroup]:
    """Group root causes by signature, ordered by descending count."""
    groups: dict[str, FailureGroup] = {}
    for root_cause in causes:
        key = _signature(root_cause)
        if key in groups:
            groups[key].count += 1
        else:
            groups[key] = FailureGroup(key=key, count=1, sampled=True, representative=root_cause)
    return sorted(groups.values(), key=lambda group: group.count, reverse=True)


def _iso(value: Any) -> str | None:  # noqa: ANN401
    """Return ISO-8601 text for a datetime, or None."""
    return value.isoformat() if value else None


def _status_name(desc: object) -> str | None:
    """Return a describe response status name, or None."""
    status = getattr(desc, "status", None)
    return getattr(status, "name", None) if status else None


def _terminal_event(history: Any) -> tuple[str, Any] | None:  # noqa: ANN401
    """Return (attr_name, attrs) for the last terminal event, or None."""
    for event in reversed(list(history.events)):
        for attr in _TERMINAL_ATTRS:
            if event.HasField(attr):
                return attr, getattr(event, attr)
    return None


def _timeout_type(failure: Any) -> str | None:  # noqa: ANN401
    """Return the first timeout type found in the cause chain, or None."""
    for link in _chain(failure):
        if link.WhichOneof("failure_info") == "timeout_failure_info":
            return _enum_name(TimeoutType, link.timeout_failure_info.timeout_type, "TIMEOUT_TYPE_")
    return None


def _last_failed_activity(failure: Any) -> LastFailedActivity | None:  # noqa: ANN401
    """Find the last activity failure in the cause chain."""
    match: LastFailedActivity | None = None
    for link in _chain(failure):
        if link.WhichOneof("failure_info") != "activity_failure_info":
            continue
        info = link.activity_failure_info
        match = LastFailedActivity(
            activity_type=info.activity_type.name or None,
            activity_id=info.activity_id or None,
            retry_state=_enum_name(RetryState, info.retry_state, "RETRY_STATE_"),
            failure=_root_cause(link.cause) if link.HasField("cause") else None,
        )
    return match


def _apply_terminal(analysis: WorkflowFailureAnalysis, terminal: tuple[str, Any]) -> WorkflowFailureAnalysis:
    """Populate failure fields on the analysis from the terminal event."""
    attr, attrs = terminal
    if attr == "workflow_execution_terminated_event_attributes":
        analysis.termination_reason = attrs.reason or None
    elif attr == "workflow_execution_failed_event_attributes":
        _apply_failure_terminal(analysis, attrs.failure)
    return analysis


def _apply_failure_terminal(analysis: WorkflowFailureAnalysis, failure: Any) -> None:  # noqa: ANN401
    """Populate failure fields on the analysis from a failure object."""
    analysis.root_cause = _root_cause(_chain(failure)[-1])
    analysis.cause_chain = _cause_links(failure)
    analysis.last_failed_activity = _last_failed_activity(failure)
    analysis.timeout_type = _timeout_type(failure)


def _group_key(group: Any) -> str:  # noqa: ANN401
    """Return the string key for a count-aggregation group."""
    group_values = getattr(group, "group_values", [])
    return str(group_values[0]) if group_values else "unknown"
