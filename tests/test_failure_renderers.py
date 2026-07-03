from temporal_mcp.models import CauseLink, FailureGroup, FailureSummary, RootCause, WorkflowFailureAnalysis
from temporal_mcp.renderers import failure_renderer


def test_failure_analysis_includes_main_heading():
    analysis = WorkflowFailureAnalysis(namespace="ns", workflow_id="wf")

    text = failure_renderer.failure_analysis(analysis)

    assert "## Workflow Failure Analysis" in text


def test_failure_analysis_includes_root_cause_section_when_present():
    analysis = WorkflowFailureAnalysis(
        namespace="ns",
        workflow_id="wf",
        root_cause=RootCause(message="boom", category="ApplicationFailure", error_type="E"),
    )

    text = failure_renderer.failure_analysis(analysis)

    assert "## Root Cause" in text


def test_failure_analysis_includes_cause_chain_section_when_present():
    analysis = WorkflowFailureAnalysis(
        namespace="ns",
        workflow_id="wf",
        cause_chain=[CauseLink(message="wrap", category="ActivityFailure")],
    )

    text = failure_renderer.failure_analysis(analysis)

    assert "## Cause Chain" in text


def test_failure_summary_includes_required_sections_when_empty():
    summary = FailureSummary(namespace="ns")

    text = failure_renderer.failure_summary(summary)

    assert "## Failure Summary" in text
    assert "## By Workflow Type" in text
    assert "## By Error Type" in text


def test_failure_groups_includes_default_title():
    groups = [FailureGroup(key="ApplicationFailure|E|boom", count=2, sampled=True)]

    text = failure_renderer.failure_groups(groups)

    assert "## Top Failure Types" in text
