"""Mappers for workflow SDK and protobuf responses."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import bytes_value_text, iso_datetime, timestamp_to_iso
from temporal_mcp.models import ClusterInfo, ExecutionDetail, ExecutionSummary, FailureInfo, HistoryEventModel


_FAILURE_ATTRS = (
    "workflow_execution_failed_event_attributes",
    "activity_task_failed_event_attributes",
    "workflow_task_failed_event_attributes",
    "workflow_execution_terminated_event_attributes",
    "workflow_execution_timed_out_event_attributes",
)
_SCHEDULED_ATTR = "activity_task_scheduled_event_attributes"
_ACTIVITY_ATTRS = (
    _SCHEDULED_ATTR,
    "activity_task_started_event_attributes",
    "activity_task_completed_event_attributes",
    "activity_task_failed_event_attributes",
    "activity_task_timed_out_event_attributes",
    "activity_task_cancel_requested_event_attributes",
    "activity_task_canceled_event_attributes",
)


def _search_attrs(execution: Any) -> dict[str, object]:  # noqa: ANN401
    """Extract typed search attributes into a plain dict."""
    out: dict[str, object] = {}
    typed = getattr(execution, "typed_search_attributes", None)
    if not typed:
        return out
    try:
        for pair in typed:
            key = getattr(pair.key, "name", str(pair.key))
            out[key] = pair.value
    except TypeError:
        pass
    return out


def execution_summary(raw: object) -> ExecutionSummary:
    """Build an ExecutionSummary from a WorkflowExecution."""
    execution = cast("Any", raw)
    return ExecutionSummary(
        namespace=execution.namespace,
        workflow_id=execution.id,
        run_id=execution.run_id,
        workflow_type=execution.workflow_type,
        task_queue=execution.task_queue,
        status=execution.status.name if execution.status else None,
        start_time=iso_datetime(execution.start_time),
        close_time=iso_datetime(execution.close_time),
        execution_time=iso_datetime(execution.execution_time),
        history_length=execution.history_length,
        parent_id=execution.parent_id,
        parent_run_id=execution.parent_run_id,
        root_id=execution.root_id,
    )


def execution_detail(raw: object) -> ExecutionDetail:
    """Build an ExecutionDetail from a WorkflowExecution."""
    base = execution_summary(raw).model_dump()
    return ExecutionDetail(**base, search_attributes=_search_attrs(cast("Any", raw)))


def _failure_of(attributes: Any) -> FailureInfo | None:  # noqa: ANN401
    """Extract FailureInfo from a failure-bearing event attribute block."""
    failure = getattr(attributes, "failure", None)
    if failure is None:
        return None
    return FailureInfo(
        message=failure.message,
        type=failure.WhichOneof("failure_info"),
        stack_trace=failure.stack_trace or None,
    )


def _event_attrs(event: Any, names: tuple[str, ...]) -> Any | None:  # noqa: ANN401
    """Return the first present attribute block from the event."""
    for name in names:
        if event.HasField(name):
            return getattr(event, name)
    return None


def _activity_identity(attributes: Any) -> tuple[str | None, str | None]:  # noqa: ANN401
    """Extract activity type and ID from scheduled-event attributes."""
    activity_type = getattr(getattr(attributes, "activity_type", None), "name", None)
    activity_id = getattr(attributes, "activity_id", None)
    return activity_type, activity_id


def _scheduled_activity_identities(events: list[Any]) -> dict[int, tuple[str | None, str | None]]:
    """Index scheduled activity event IDs to activity identity."""
    identities: dict[int, tuple[str | None, str | None]] = {}
    for event in events:
        if event.HasField(_SCHEDULED_ATTR):
            identities[event.event_id] = _activity_identity(getattr(event, _SCHEDULED_ATTR))
    return identities


def _correlated_identity(
    attrs: object, identities: dict[int, tuple[str | None, str | None]]
) -> tuple[str | None, str | None]:
    """Return identity from an activity attr block or its scheduled event."""
    direct_type, direct_id = _activity_identity(attrs)
    if direct_type or direct_id:
        return direct_type, direct_id
    return identities.get(getattr(attrs, "scheduled_event_id", 0), (None, None))


def _history_event(event: object, identities: dict[int, tuple[str | None, str | None]]) -> HistoryEventModel:
    """Build one HistoryEventModel from a raw history event."""
    history_event = cast("Any", event)
    failure, reason = _failure_and_reason(history_event)
    activity_type, activity_id = _activity_for_event(history_event, identities)
    return HistoryEventModel(
        event_id=history_event.event_id,
        event_time=timestamp_to_iso(history_event.event_time) if history_event.event_time else None,
        event_type=history_event.event_type.name
        if hasattr(history_event.event_type, "name")
        else str(history_event.event_type),
        failure=failure,
        reason=reason,
        activity_type=activity_type,
        activity_id=activity_id,
    )


def _failure_and_reason(event: Any) -> tuple[FailureInfo | None, str | None]:  # noqa: ANN401
    """Extract failure and reason details from a history event."""
    for attr in _FAILURE_ATTRS:
        if event.HasField(attr):
            sub = getattr(event, attr)
            return _failure_of(sub), getattr(sub, "reason", None) or None
    return None, None


def _activity_for_event(
    event: object, identities: dict[int, tuple[str | None, str | None]]
) -> tuple[str | None, str | None]:
    """Extract or correlate activity identity for a history event."""
    attrs = _event_attrs(event, _ACTIVITY_ATTRS)
    if attrs is None:
        return None, None
    return _correlated_identity(attrs, identities)


def history_events(raw: object) -> list[HistoryEventModel]:
    """Build a compact, failure-focused list of history events."""
    events = list(cast("Any", raw).events)
    identities = _scheduled_activity_identities(events)
    return [_history_event(event, identities) for event in events]


def cluster_info(raw: object) -> ClusterInfo:
    """Build ClusterInfo from a GetSystemInfo response."""
    response = cast("Any", raw)
    caps = response.capabilities
    return ClusterInfo(
        server_version=response.server_version,
        capabilities={
            "signal_and_query_header": caps.signal_and_query_header,
            "internal_error_differentiation": caps.internal_error_differentiation,
            "activity_failure_include_heartbeat": caps.activity_failure_include_heartbeat,
            "supports_schedules": caps.supports_schedules,
            "encoded_failure_attributes": caps.encoded_failure_attributes,
            "build_id_based_versioning": caps.build_id_based_versioning,
            "upsert_memo": caps.upsert_memo,
            "eager_workflow_start": caps.eager_workflow_start,
        },
    )


def count_payload(namespace: str, query: str | None, raw: object) -> dict[str, object]:
    """Build workflow count payload with decoded group values."""
    response = cast("Any", raw)
    groups = [
        {"count": group.count, "values": [bytes_value_text(value) for value in group.group_values]}
        for group in response.groups
    ]
    return {"namespace": namespace, "query": query, "count": response.count, "groups": groups}
