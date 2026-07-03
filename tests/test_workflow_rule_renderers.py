"""Tests for workflow rule renderers."""

from temporal_mcp.models import WorkflowRuleDetail, WorkflowRuleSummary
from temporal_mcp.renderers import workflow_rule_renderer


def test_workflow_rule_list_renders_table() -> None:
    text = workflow_rule_renderer.workflow_rule_list(
        [WorkflowRuleSummary(id="rule-1", visibility_query="WorkflowType='Payment'")]
    )
    assert "## Workflow Rules" in text
    assert "| id | visibility_query | description | create_time |" in text
    assert "rule-1" in text


def test_workflow_rule_detail_renders_detail_block() -> None:
    text = workflow_rule_renderer.workflow_rule_detail(WorkflowRuleDetail(id="rule-1", actions=["pause", None]))
    assert "## Workflow Rule" in text
    assert "**actions**" in text
    assert "pause" in text
