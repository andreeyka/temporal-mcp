"""Tests for workflow-rule mappers."""

from datetime import UTC, datetime

from google.protobuf.timestamp_pb2 import Timestamp
from temporalio.api.rules.v1 import WorkflowRule, WorkflowRuleAction, WorkflowRuleSpec

from temporal_mcp.mappers import workflow_rule_mapper as mapper
from temporal_mcp.models import WorkflowRuleDetail, WorkflowRuleSummary


def _ts():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 1, 1, tzinfo=UTC))
    return ts


def _rule(**spec_kwargs):
    spec = WorkflowRuleSpec(id="rule-1", visibility_query="WorkflowType='foo'", **spec_kwargs)
    return WorkflowRule(create_time=_ts(), spec=spec, created_by_identity="alice", description="a rule")


def test_workflow_rule_summary_shapes_fields():
    out = mapper.workflow_rule_summary(_rule())
    assert isinstance(out, WorkflowRuleSummary)
    assert out.model_dump(mode="json") == {
        "id": "rule-1",
        "visibility_query": "WorkflowType='foo'",
        "description": "a rule",
        "created_by_identity": "alice",
        "create_time": _ts().ToDatetime().isoformat(),
    }


def test_workflow_rule_summary_handles_missing_create_time():
    rule = WorkflowRule(spec=WorkflowRuleSpec(id="rule-2", visibility_query="q"))
    assert mapper.workflow_rule_summary(rule).create_time is None


def test_workflow_rule_detail_includes_actions_and_expiration():
    action = WorkflowRuleAction(activity_pause=WorkflowRuleAction.ActionActivityPause())
    out = mapper.workflow_rule_detail(_rule(actions=[action], expiration_time=_ts()))
    assert isinstance(out, WorkflowRuleDetail)
    assert out.actions == ["activity_pause"]
    assert out.expiration_time == _ts().ToDatetime().isoformat()
    assert out.id == "rule-1"
    assert out.visibility_query == "WorkflowType='foo'"


def test_workflow_rule_detail_preserves_unset_action_variant():
    out = mapper.workflow_rule_detail(_rule(actions=[WorkflowRuleAction()]))
    assert out.actions == [None]


def test_workflow_rule_detail_handles_missing_expiration():
    out = mapper.workflow_rule_detail(_rule())
    assert out.expiration_time is None
    assert out.actions == []


def test_workflow_rule_summaries_maps_each_rule():
    assert mapper.workflow_rule_summaries([_rule()]) == [mapper.workflow_rule_summary(_rule())]
