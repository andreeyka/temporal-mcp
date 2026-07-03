"""Tests for workflow mappers."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import ClassVar

from temporalio.api.enums.v1 import TimeoutType
from temporalio.api.failure.v1 import ApplicationFailureInfo, Failure, TimeoutFailureInfo
from temporalio.api.history.v1 import ActivityTaskFailedEventAttributes
from temporalio.client import WorkflowExecutionStatus

from temporal_mcp.mappers import workflow_mapper


class _FakeExec:
    namespace = "ns-a"
    id = "wf-1"
    run_id = "r1"
    workflow_type = "MyWF"
    task_queue = "tq"
    status = WorkflowExecutionStatus.FAILED
    start_time = datetime(2026, 1, 1, tzinfo=UTC)
    close_time = None
    execution_time = None
    history_length = 42
    parent_id = None
    parent_run_id = None
    root_id = None
    typed_search_attributes = None


def test_execution_summary_maps_execution_fields() -> None:
    summary = workflow_mapper.execution_summary(_FakeExec())

    assert summary.namespace == "ns-a"
    assert summary.status == "FAILED"
    assert summary.history_length == 42
    assert summary.start_time == datetime(2026, 1, 1, tzinfo=UTC).isoformat()


def test_execution_detail_adds_search_attributes() -> None:
    raw = _FakeExec()
    raw.typed_search_attributes = [SimpleNamespace(key=SimpleNamespace(name="CustomKeyword"), value="alpha")]

    detail = workflow_mapper.execution_detail(raw)

    assert detail.workflow_id == "wf-1"
    assert detail.search_attributes == {"CustomKeyword": "alpha"}


class _FakeFailure:
    def __init__(self, message: str, stack_trace: str | None = None) -> None:
        self.message = message
        self.stack_trace = stack_trace

    def WhichOneof(self, name):  # noqa: N802
        assert name == "failure_info"
        return "timeout_failure_info"


class _FakeFailedAttrs:
    scheduled_event_id = 10
    failure = _FakeFailure("boom", "trace")


class _FakeEventTime:
    def ToDatetime(self):  # noqa: N802
        return datetime(2026, 1, 1, tzinfo=UTC)


class _FakeHistoryEvent:
    def __init__(self, event_id: int, event_type: str, attr_name: str, attrs: object) -> None:
        self.event_id = event_id
        self.event_time = _FakeEventTime()
        self.event_type = SimpleNamespace(name=event_type)
        setattr(self, attr_name, attrs)
        self._attr_name = attr_name

    def HasField(self, name):  # noqa: N802
        return name == self._attr_name


class _FakeHistory:
    events: ClassVar = [
        _FakeHistoryEvent(
            1,
            "EVENT_TYPE_WORKFLOW_EXECUTION_FAILED",
            "workflow_execution_failed_event_attributes",
            _FakeFailedAttrs(),
        )
    ]


def test_history_events_extracts_failure() -> None:
    events = workflow_mapper.history_events(_FakeHistory())

    assert len(events) == 1
    event = events[0]
    assert event.event_id == 1
    assert event.event_type == "EVENT_TYPE_WORKFLOW_EXECUTION_FAILED"
    assert event.event_time == datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    assert event.failure is not None
    assert event.failure.message == "boom"
    assert event.failure.stack_trace == "trace"
    assert event.failure.type == "timeout_failure_info"
    assert event.reason is None


def test_history_events_map_scheduled_activity_identity() -> None:
    attrs = SimpleNamespace(activity_type=SimpleNamespace(name="ChargeCard"), activity_id="activity-1")
    history = SimpleNamespace(
        events=[
            _FakeHistoryEvent(
                10,
                "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED",
                "activity_task_scheduled_event_attributes",
                attrs,
            )
        ]
    )

    event = workflow_mapper.history_events(history)[0]

    assert event.activity_type == "ChargeCard"
    assert event.activity_id == "activity-1"


def test_history_events_correlate_activity_identity_from_scheduled_event() -> None:
    scheduled_attrs = SimpleNamespace(activity_type=SimpleNamespace(name="ChargeCard"), activity_id="activity-1")
    failed_attrs = SimpleNamespace(scheduled_event_id=10, failure=_FakeFailure("boom"))
    history = SimpleNamespace(
        events=[
            _FakeHistoryEvent(
                10,
                "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED",
                "activity_task_scheduled_event_attributes",
                scheduled_attrs,
            ),
            _FakeHistoryEvent(
                12,
                "EVENT_TYPE_ACTIVITY_TASK_FAILED",
                "activity_task_failed_event_attributes",
                failed_attrs,
            ),
        ]
    )

    event = workflow_mapper.history_events(history)[1]

    assert event.activity_type == "ChargeCard"
    assert event.activity_id == "activity-1"


def _failure_history(failure: Failure) -> SimpleNamespace:
    attrs = ActivityTaskFailedEventAttributes(failure=failure)
    event = _FakeHistoryEvent(1, "EVENT_TYPE_ACTIVITY_TASK_FAILED", "activity_task_failed_event_attributes", attrs)
    return SimpleNamespace(events=[event])


def test_history_events_extracts_real_timeout_failure_variant() -> None:
    failure = Failure(
        message="activity timed out",
        timeout_failure_info=TimeoutFailureInfo(timeout_type=TimeoutType.TIMEOUT_TYPE_START_TO_CLOSE),
    )

    info = workflow_mapper.history_events(_failure_history(failure))[0].failure

    assert info is not None
    assert info.message == "activity timed out"
    assert info.type == "timeout_failure_info"


def test_history_events_extracts_real_application_failure_variant() -> None:
    failure = Failure(message="boom", application_failure_info=ApplicationFailureInfo(type="MyError"))

    info = workflow_mapper.history_events(_failure_history(failure))[0].failure

    assert info is not None
    assert info.message == "boom"
    assert info.type == "application_failure_info"


def test_history_events_extracts_real_failure_without_variant() -> None:
    failure = Failure(message="plain failure")

    info = workflow_mapper.history_events(_failure_history(failure))[0].failure

    assert info is not None
    assert info.message == "plain failure"
    assert info.type is None


def test_history_events_correlate_real_failed_activity_identity() -> None:
    scheduled_attrs = SimpleNamespace(activity_type=SimpleNamespace(name="ChargeCard"), activity_id="activity-1")
    failure = Failure(message="boom", application_failure_info=ApplicationFailureInfo(type="MyError"))
    failed_attrs = ActivityTaskFailedEventAttributes(scheduled_event_id=10, failure=failure)
    history = SimpleNamespace(
        events=[
            _FakeHistoryEvent(
                10,
                "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED",
                "activity_task_scheduled_event_attributes",
                scheduled_attrs,
            ),
            _FakeHistoryEvent(
                12,
                "EVENT_TYPE_ACTIVITY_TASK_FAILED",
                "activity_task_failed_event_attributes",
                failed_attrs,
            ),
        ]
    )

    event = workflow_mapper.history_events(history)[1]

    assert event.activity_type == "ChargeCard"
    assert event.activity_id == "activity-1"
    assert event.failure is not None


class _FakeCapabilities:
    signal_and_query_header = True
    internal_error_differentiation = False
    activity_failure_include_heartbeat = True
    supports_schedules = True
    encoded_failure_attributes = False
    build_id_based_versioning = True
    upsert_memo = False
    eager_workflow_start = True


class _FakeSystemInfoResp:
    server_version = "1.24.0"
    capabilities = _FakeCapabilities()


def test_cluster_info_maps_capabilities() -> None:
    info = workflow_mapper.cluster_info(_FakeSystemInfoResp())

    assert info.server_version == "1.24.0"
    assert info.capabilities["supports_schedules"] is True
    assert info.capabilities["internal_error_differentiation"] is False


def test_count_payload_maps_group_values_to_text() -> None:
    raw = SimpleNamespace(
        count=3,
        groups=[SimpleNamespace(count=2, group_values=[SimpleNamespace(data=b"FAILED"), b"TypeA"])],
    )

    payload = workflow_mapper.count_payload("default", "ExecutionStatus='Failed'", raw)

    assert payload == {
        "namespace": "default",
        "query": "ExecutionStatus='Failed'",
        "count": 3,
        "groups": [{"count": 2, "values": ["FAILED", "TypeA"]}],
    }
