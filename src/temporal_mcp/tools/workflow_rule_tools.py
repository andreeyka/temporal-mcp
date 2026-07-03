"""Workflow-rule MCP tools (list/describe/create/delete)."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import workflow_rule_mapper
from temporal_mcp.providers import TemporalWorkflowRuleServiceProvider
from temporal_mcp.renderers import workflow_rule_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.workflow_rule_service import TemporalWorkflowRuleService  # noqa: TC001
from temporal_mcp.tool_annotations import mutating, read_only, write
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_action_result, make_tool_result


temporal_workflow_rule_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
RuleId = Annotated[str, Field(description="Workflow rule id")]
IsoTime = Annotated[
    str,
    Field(
        description='ISO-8601 timestamp, e.g. "2026-01-01T00:00:00Z"',
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
    ),
]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.WORKFLOW_RULE, TemporalToolTags.READ}
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.WORKFLOW_RULE, TemporalToolTags.MUTATING}


@temporal_workflow_rule_mcp.tool(tags=READ_TAGS, annotations=read_only("List Workflow Rules"))
async def list_workflow_rules(
    namespace: Namespace,
    *,
    structured_content: StructuredContent = False,
    workflow_rule_service: TemporalWorkflowRuleService = TemporalWorkflowRuleServiceProvider,
) -> ToolResult:
    """List all workflow rules in a namespace.

    Args:
        namespace: Target namespace.
        structured_content: Return structured content for programmatic use.
        workflow_rule_service: Workflow-rule service (injected).

    Returns:
        ToolResult with the rule list as Markdown text and optional structured content.
    """
    items = workflow_rule_mapper.workflow_rule_summaries(await workflow_rule_service.list_workflow_rules(namespace))
    return make_tool_result(
        workflow_rule_renderer.workflow_rule_list(items),
        structured_content=structured_content,
        structured={"workflow_rules": items},
    )


@temporal_workflow_rule_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Workflow Rule"))
async def describe_workflow_rule(
    namespace: Namespace,
    rule_id: RuleId,
    *,
    structured_content: StructuredContent = False,
    workflow_rule_service: TemporalWorkflowRuleService = TemporalWorkflowRuleServiceProvider,
) -> ToolResult:
    """Describe one workflow rule, including its actions and expiration.

    Args:
        namespace: Target namespace.
        rule_id: Workflow rule id.
        structured_content: Return structured content for programmatic use.
        workflow_rule_service: Workflow-rule service (injected).

    Returns:
        ToolResult with the rule detail as Markdown text and optional structured content.
    """
    detail = workflow_rule_mapper.workflow_rule_detail(
        await workflow_rule_service.describe_workflow_rule(namespace, rule_id)
    )
    return make_tool_result(
        workflow_rule_renderer.workflow_rule_detail(detail),
        structured_content=structured_content,
        structured={"workflow_rule": detail},
    )


@temporal_workflow_rule_mcp.tool(tags=MUTATE_TAGS, annotations=write("Create Workflow Rule"))
async def create_workflow_rule(
    namespace: Namespace,
    rule_id: RuleId,
    visibility_query: Annotated[str, Field(description="Visibility query selecting target workflows")],
    description: Annotated[str, Field(description="Human-readable description of the rule")] = "",
    expiration: IsoTime | None = None,
    *,
    structured_content: StructuredContent = False,
    workflow_rule_service: TemporalWorkflowRuleService = TemporalWorkflowRuleServiceProvider,
) -> ToolResult:
    """Create a workflow rule that pauses activities matching a visibility query. (Mutating).

    Args:
        namespace: Target namespace.
        rule_id: Id to assign to the new rule.
        visibility_query: Visibility query selecting target workflows.
        description: Human-readable description of the rule.
        expiration: Optional ISO-8601 expiration timestamp.
        structured_content: Return structured content for programmatic use.
        workflow_rule_service: Workflow-rule service (injected).

    Returns:
        ToolResult confirming creation as Markdown text and optional structured content.
    """
    created_id = await workflow_rule_service.create_workflow_rule(
        namespace, rule_id, visibility_query, description, expiration
    )
    payload = {"rule_id": created_id, "created": True}
    return make_action_result(payload, "Workflow Rule Created", structured_content=structured_content)


@temporal_workflow_rule_mcp.tool(tags=MUTATE_TAGS, annotations=mutating("Delete Workflow Rule"))
async def delete_workflow_rule(
    namespace: Namespace,
    rule_id: RuleId,
    *,
    structured_content: StructuredContent = False,
    workflow_rule_service: TemporalWorkflowRuleService = TemporalWorkflowRuleServiceProvider,
) -> ToolResult:
    """Delete a workflow rule. (Destructive).

    Args:
        namespace: Target namespace.
        rule_id: Workflow rule id to delete.
        structured_content: Return structured content for programmatic use.
        workflow_rule_service: Workflow-rule service (injected).

    Returns:
        ToolResult confirming deletion as Markdown text and optional structured content.
    """
    await workflow_rule_service.delete_workflow_rule(namespace, rule_id)
    payload = {"rule_id": rule_id, "deleted": True}
    return make_action_result(payload, "Workflow Rule Deleted", structured_content=structured_content)
