from temporal_mcp.models import (
    CauseLink,
    FailureGroup,
    FailureSummary,
    LastFailedActivity,
    RootCause,
    WorkflowFailureAnalysis,
)


def test_root_cause_defaults():
    rc = RootCause(message="boom", category="ApplicationFailure")
    assert rc.error_type is None
    assert rc.stack_trace is None


def test_analysis_defaults_empty_chain():
    a = WorkflowFailureAnalysis(namespace="ns", workflow_id="wf")
    assert a.cause_chain == []
    assert a.root_cause is None
    assert a.last_failed_activity is None


def test_summary_holds_groups():
    s = FailureSummary(
        namespace="ns",
        total_failed=3,
        by_workflow_type=[FailureGroup(key="MyWF", count=3)],
        by_error_type=[FailureGroup(key="ApplicationFailure||boom", count=2, sampled=True)],
        sample_size=100,
        note="sampled",
    )
    assert s.by_workflow_type[0].count == 3
    assert s.by_error_type[0].sampled is True


def test_cause_link_and_activity():
    link = CauseLink(message="m", category="ActivityFailure")
    act = LastFailedActivity(activity_type="A", failure=RootCause(message="m", category="ApplicationFailure"))
    assert link.error_type is None
    assert act.failure.category == "ApplicationFailure"
