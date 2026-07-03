"""Render workflow rule output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import WorkflowRuleDetail, WorkflowRuleSummary


_ENTITY_RENDERER = EntityRenderer()
_WORKFLOW_RULE_COLUMNS = ("id", "visibility_query", "description", "create_time")
_WORKFLOW_RULE_SPEC = RenderSpec(title="Workflow Rules", columns=_WORKFLOW_RULE_COLUMNS)


def workflow_rule_list(items: list[WorkflowRuleSummary]) -> str:
    """Render workflow rule summaries as Markdown.

    Args:
        items: Workflow rule summaries to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.list(items, _WORKFLOW_RULE_SPEC)


def workflow_rule_detail(detail: WorkflowRuleDetail) -> str:
    """Render one workflow rule as Markdown.

    Args:
        detail: Workflow rule detail to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.detail(detail, "Workflow Rule")
