"""Mappers for workflow rule protobuf objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import oneof_name, timestamp_field_to_iso
from temporal_mcp.models import WorkflowRuleDetail, WorkflowRuleSummary


# Any is constrained to protobuf mapper boundaries with dynamic attributes.


def _action_kind(raw: object) -> str | None:
    action = cast("Any", raw)
    return oneof_name(action, "variant")


def workflow_rule_summary(raw: object) -> WorkflowRuleSummary:
    """Map a workflow rule proto to a workflow rule summary model."""
    rule = cast("Any", raw)
    return WorkflowRuleSummary(
        id=rule.spec.id,
        visibility_query=rule.spec.visibility_query,
        description=rule.description,
        created_by_identity=rule.created_by_identity,
        create_time=timestamp_field_to_iso(rule, "create_time"),
    )


def workflow_rule_detail(raw: object) -> WorkflowRuleDetail:
    """Map a workflow rule proto to a workflow rule detail model."""
    rule = cast("Any", raw)
    summary = workflow_rule_summary(raw).model_dump()
    return WorkflowRuleDetail(
        **summary,
        actions=[_action_kind(action) for action in rule.spec.actions],
        expiration_time=timestamp_field_to_iso(rule.spec, "expiration_time"),
    )


def workflow_rule_summaries(raw: list[object]) -> list[WorkflowRuleSummary]:
    """Map workflow rule protos to workflow rule summary models."""
    return [workflow_rule_summary(rule) for rule in raw]
