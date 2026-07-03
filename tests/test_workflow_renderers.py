"""Tests for workflow renderers."""

from temporal_mcp.models import ClusterInfo, ExecutionDetail, ExecutionSummary, FailureInfo, HistoryEventModel
from temporal_mcp.renderers import workflow_renderer


def test_execution_list_renders_table() -> None:
    text = workflow_renderer.execution_list(
        [
            ExecutionSummary(
                namespace="default",
                workflow_id="wf-1",
                close_time="2026-01-01T00:00:00+00:00",
                history_length=12,
                root_id="root-1",
            )
        ]
    )

    assert "## Workflows" in text
    assert "close_time" in text
    assert "history_length" in text
    assert "wf-1" in text
    assert "2026-01-01T00:00:00+00:00" in text
    assert "12" in text
    assert "root-1" in text


def test_execution_detail_renders_search_attributes_section() -> None:
    detail = ExecutionDetail(namespace="default", workflow_id="wf-1", search_attributes={"CustomKeyword": "alpha"})

    text = workflow_renderer.execution_detail(detail)

    assert "## Workflow" in text
    assert "### Search Attributes" in text
    assert "CustomKeyword" in text


def test_history_renders_events_with_activity_identity() -> None:
    event = HistoryEventModel(
        event_id=12,
        event_type="EVENT_TYPE_ACTIVITY_TASK_COMPLETED",
        activity_type="ChargeCard",
        activity_id="activity-1",
    )
    payload = {"namespace": "default", "workflow_id": "wf-1", "run_id": None, "events": [event.model_dump()]}

    text = workflow_renderer.history(payload)

    assert "## Workflow History" in text
    assert "## Events" in text
    assert "| event_id | event_time | event_type | reason | activity_type | activity_id |" in text
    assert "ChargeCard" in text
    assert "activity-1" in text


def test_history_renders_failure_details() -> None:
    event = HistoryEventModel(
        event_id=13,
        event_type="EVENT_TYPE_WORKFLOW_EXECUTION_FAILED",
        failure=FailureInfo(message="boom", type="ApplicationError", stack_trace="line 1\nline 2"),
    )
    payload = {"namespace": "default", "workflow_id": "wf-1", "run_id": None, "events": [event.model_dump()]}

    text = workflow_renderer.history(payload)

    assert "## Failures" in text
    assert "ApplicationError" in text
    assert "boom" in text
    assert "line 1 line 2" in text


def test_history_renders_empty_events_section() -> None:
    payload = {"namespace": "default", "workflow_id": "wf-1", "run_id": None, "events": []}

    text = workflow_renderer.history(payload)

    assert "## Workflow History" in text
    assert "## Events" in text
    assert "_No items._" in text


def test_count_renders_groups() -> None:
    payload = {"namespace": "default", "query": None, "count": 2, "groups": [{"count": 2, "values": ["FAILED"]}]}

    text = workflow_renderer.count(payload)

    assert "## Workflow Count" in text
    assert "## Groups" in text
    assert "FAILED" in text


def test_count_renders_empty_groups_section() -> None:
    payload = {"namespace": "default", "query": None, "count": 0, "groups": []}

    text = workflow_renderer.count(payload)

    assert "## Workflow Count" in text
    assert "## Groups" in text
    assert "_No items._" in text


def test_cluster_info_renders_capabilities() -> None:
    info = ClusterInfo(server_version="1.24.0", capabilities={"supports_schedules": True})

    text = workflow_renderer.cluster_info(info)

    assert "## Cluster Info" in text
    assert "### Capabilities" in text
    assert "supports_schedules" in text
