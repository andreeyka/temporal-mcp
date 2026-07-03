from datetime import UTC, datetime
from types import SimpleNamespace

from temporalio.api.enums.v1 import TimeoutType

from temporal_mcp.mappers import failure_mapper
from temporal_mcp.models import FailureGroup, RootCause, WorkflowFailureAnalysis


def _fail(message="", *, info=None, info_val=None, source="", stack="", cause=None):
    """Build a fake Temporal Failure-like object."""

    class _F:
        def __init__(self):
            self.message = message
            self.source = source
            self.stack_trace = stack
            self.cause = cause

        def WhichOneof(self, oneof):  # noqa: N802
            assert oneof == "failure_info"
            return info

        def HasField(self, name):  # noqa: N802
            return name == "cause" and cause is not None

    failure = _F()
    if info:
        setattr(failure, info, info_val)
    return failure


class _Event:
    def __init__(self, attr, value):
        self._attr = attr
        setattr(self, attr, value)

    def HasField(self, name):  # noqa: N802
        return name == self._attr


class _History:
    def __init__(self, events):
        self.events = events


def _failure_event(failure):
    return _History([_Event("workflow_execution_failed_event_attributes", SimpleNamespace(failure=failure))])


def test_root_cause_of_history_from_failed_event():
    inner = _fail("root", info="application_failure_info", info_val=SimpleNamespace(type="Deep"))
    outer = _fail("wrap", info="activity_failure_info", info_val=SimpleNamespace(), cause=inner)

    root_cause = failure_mapper.root_cause_of_history(_failure_event(outer))

    assert root_cause.message == "root"


def test_root_cause_of_history_none_when_not_failed():
    history = _History([_Event("workflow_execution_started_event_attributes", SimpleNamespace())])

    assert failure_mapper.root_cause_of_history(history) is None


def test_root_causes_of_histories_filters_non_failed_histories():
    failed = _failure_event(_fail("root", info="application_failure_info", info_val=SimpleNamespace(type="Deep")))
    started = _History([_Event("workflow_execution_started_event_attributes", SimpleNamespace())])

    causes = failure_mapper.root_causes_of_histories([failed, started])

    assert [cause.message for cause in causes] == ["root"]


def test_build_analysis_failed_with_activity():
    inner = _fail("root", info="application_failure_info", info_val=SimpleNamespace(type="Deep"))
    activity_info = SimpleNamespace(
        activity_type=SimpleNamespace(name="MyActivity"),
        activity_id="a1",
        retry_state=0,
    )
    outer = _fail("wrap", info="activity_failure_info", info_val=activity_info, cause=inner)
    desc = SimpleNamespace(status=SimpleNamespace(name="FAILED"), workflow_type="MyWF", close_time=None, run_id="r1")

    analysis = failure_mapper.build_analysis("ns", "wf", None, desc, _failure_event(outer))

    assert analysis.status == "FAILED"
    assert analysis.workflow_type == "MyWF"
    assert analysis.run_id == "r1"
    assert analysis.root_cause.message == "root"
    assert [cause.category for cause in analysis.cause_chain] == ["ActivityFailure", "ApplicationFailure"]
    assert analysis.last_failed_activity.activity_type == "MyActivity"
    assert analysis.last_failed_activity.failure.message == "root"


def test_build_analysis_sets_close_time():
    desc = SimpleNamespace(
        status=SimpleNamespace(name="FAILED"),
        workflow_type="MyWF",
        close_time=datetime(2026, 1, 2, tzinfo=UTC),
        run_id="r1",
    )

    analysis = failure_mapper.build_analysis("ns", "wf", None, desc, _failure_event(_fail("root")))

    assert analysis.close_time.startswith("2026-01-02")


def test_build_analysis_failed_branch_sets_timeout_type():
    inner = _fail(
        "timed out",
        info="timeout_failure_info",
        info_val=SimpleNamespace(timeout_type=TimeoutType.TIMEOUT_TYPE_START_TO_CLOSE),
    )
    activity_info = SimpleNamespace(activity_type=SimpleNamespace(name="MyActivity"), activity_id="a1", retry_state=0)
    outer = _fail("wrap", info="activity_failure_info", info_val=activity_info, cause=inner)
    desc = SimpleNamespace(status=SimpleNamespace(name="FAILED"), workflow_type="W", close_time=None, run_id="r")

    analysis = failure_mapper.build_analysis("ns", "wf", "r", desc, _failure_event(outer))

    assert analysis.timeout_type == "START_TO_CLOSE"


def test_build_analysis_reports_canceled_root_cause():
    canceled = _fail("canceled", info="canceled_failure_info", info_val=SimpleNamespace())
    desc = SimpleNamespace(status=SimpleNamespace(name="FAILED"), workflow_type="W", close_time=None, run_id="r")

    analysis = failure_mapper.build_analysis("ns", "wf", "r", desc, _failure_event(canceled))

    assert analysis.root_cause.category == "CanceledFailure"
    assert analysis.timeout_type is None


def test_build_analysis_terminated_sets_reason():
    history = _History(
        [_Event("workflow_execution_terminated_event_attributes", SimpleNamespace(reason="ops killed it"))]
    )
    desc = SimpleNamespace(status=SimpleNamespace(name="TERMINATED"), workflow_type="W", close_time=None, run_id="r")

    analysis = failure_mapper.build_analysis("ns", "wf", "r", desc, history)

    assert analysis.termination_reason == "ops killed it"
    assert analysis.root_cause is None


def test_build_analysis_no_terminal_event_is_empty():
    history = _History([_Event("workflow_execution_started_event_attributes", SimpleNamespace())])
    desc = SimpleNamespace(status=SimpleNamespace(name="RUNNING"), workflow_type="W", close_time=None, run_id="r")

    analysis = failure_mapper.build_analysis("ns", "wf", "r", desc, history)

    assert analysis.root_cause is None
    assert analysis.cause_chain == []


def test_build_analysis_uses_innermost_failed_activity():
    root = _fail("root cause", info="application_failure_info", info_val=SimpleNamespace(type="RootErr"))
    middle_info = SimpleNamespace(activity_type=SimpleNamespace(name="ActivityA"), activity_id="a1", retry_state=0)
    middle = _fail("activity a failed", info="activity_failure_info", info_val=middle_info, cause=root)
    outer_info = SimpleNamespace(activity_type=SimpleNamespace(name="ActivityB"), activity_id="b1", retry_state=0)
    outer = _fail("activity b failed", info="activity_failure_info", info_val=outer_info, cause=middle)
    desc = SimpleNamespace(status=SimpleNamespace(name="FAILED"), workflow_type="W", close_time=None, run_id="r")

    analysis = failure_mapper.build_analysis("ns", "wf", "r", desc, _failure_event(outer))

    assert analysis.last_failed_activity.activity_id == "a1"
    assert analysis.last_failed_activity.activity_type == "ActivityA"


def test_build_summary_maps_groups_and_sample():
    count = SimpleNamespace(
        count=5,
        groups=[
            SimpleNamespace(count=3, group_values=["MyWF"]),
            SimpleNamespace(count=2, group_values=["OtherWF"]),
        ],
    )
    causes = [RootCause(message="boom", category="ApplicationFailure", error_type="E")]

    summary = failure_mapper.build_summary("ns", None, count, causes, 100)

    assert summary.total_failed == 5
    assert summary.by_workflow_type[0].key == "MyWF"
    assert summary.by_workflow_type[0].count == 3
    assert summary.by_error_type[0].count == 1
    assert summary.sample_size == 100
    assert summary.note


def test_top_groups_ranks_and_truncates():
    causes = [
        RootCause(message="a", category="ApplicationFailure", error_type="E1"),
        RootCause(message="a", category="ApplicationFailure", error_type="E1"),
        RootCause(message="b", category="TimeoutFailure"),
    ]

    groups = failure_mapper.top_groups(causes, 1)

    assert len(groups) == 1
    assert isinstance(groups[0], FailureGroup)
    assert groups[0].count == 2


def test_top_groups_aggregates_by_first_message_line():
    causes = [
        RootCause(message="boom\nline2", category="ApplicationFailure", error_type="E"),
        RootCause(message="boom\nother", category="ApplicationFailure", error_type="E"),
        RootCause(message="nope", category="TimeoutFailure"),
    ]

    groups = failure_mapper.top_groups(causes, 10)

    assert groups[0].count == 2
    assert groups[0].key == "ApplicationFailure|E|boom"
    assert groups[0].sampled is True
    assert groups[0].representative.message.startswith("boom")


def test_build_analysis_can_start_from_existing_analysis_contract():
    analysis = WorkflowFailureAnalysis(namespace="ns", workflow_id="wf")

    assert analysis.cause_chain == []
