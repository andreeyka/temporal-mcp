"""Workflow read MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import workflow_mapper
from temporal_mcp.providers import TemporalWorkflowServiceProvider
from temporal_mcp.renderers import workflow_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.workflow_service import TemporalWorkflowService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_tool_result


temporal_workflow_read_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
WorkflowId = Annotated[str, Field(description="Workflow id")]
RunId = Annotated[str | None, Field(description="Run id (optional)")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.WORKFLOW, TemporalToolTags.READ}


@temporal_workflow_read_mcp.tool(tags=READ_TAGS, annotations=read_only("List Workflows"))
async def list_workflows(
    namespace: Namespace,
    query: Annotated[str | None, Field(description='Visibility query, e.g. WorkflowType="Foo"')] = None,
    status: Annotated[str | None, Field(description="Status filter (FAILED, RUNNING, ...)")] = None,
    limit: Annotated[int, Field(description="Max executions", ge=1, le=1000)] = 50,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """List or search executions in a namespace.

    Args:
        namespace: Target namespace.
        query: Optional visibility query.
        status: Optional status convenience filter, ANDed into the query.
        limit: Maximum number of executions.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the execution list as Markdown text and optional structured content.

    Raises:
        UnknownWorkflowStatusError: If status is not a valid status.
    """
    raw = await workflow_service.list_workflows(namespace, query=query, status=status, limit=limit)
    items = [workflow_mapper.execution_summary(e) for e in raw]
    return make_tool_result(
        workflow_renderer.execution_list(items),
        structured_content=structured_content,
        structured={"workflows": items},
    )


@temporal_workflow_read_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Workflow"))
async def describe_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Get status, type, task queue, timing, and search attributes for one execution.

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with execution detail as Markdown text and optional structured content.
    """
    detail = workflow_mapper.execution_detail(await workflow_service.describe_workflow(namespace, workflow_id, run_id))
    return make_tool_result(
        workflow_renderer.execution_detail(detail),
        structured_content=structured_content,
        structured=detail.model_dump(),
    )


@temporal_workflow_read_mcp.tool(tags=READ_TAGS, annotations=read_only("Get Workflow History"))
async def get_workflow_history(
    namespace: Namespace,
    workflow_id: WorkflowId,
    run_id: RunId = None,
    *,
    include_payloads: Annotated[
        bool, Field(description="Include decoded event payloads (input/result). May expose sensitive data.")
    ] = False,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Get event history with failures, reasons, and stack traces surfaced.

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        run_id: Optional run id.
        include_payloads: Include decoded workflow/activity input and result payloads.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the event list as Markdown text and optional structured content.
    """
    hist = await workflow_service.get_workflow_history(namespace, workflow_id, run_id)
    events = workflow_mapper.history_events(hist, include_payloads=include_payloads)
    payload = {
        "namespace": namespace,
        "workflow_id": workflow_id,
        "run_id": run_id,
        "events": [e.model_dump() for e in events],
    }
    return make_tool_result(
        workflow_renderer.history(payload),
        structured_content=structured_content,
        structured=payload,
    )


@temporal_workflow_read_mcp.tool(tags=READ_TAGS, annotations=read_only("Count Workflows"))
async def count_workflows(
    namespace: Namespace,
    query: Annotated[str | None, Field(description="Visibility query")] = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Count executions matching a visibility query (cheap aggregate).

    Args:
        namespace: Target namespace.
        query: Optional visibility query.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with count and group breakdown as Markdown text and optional structured content.
    """
    resp = await workflow_service.count_workflows(namespace, query)
    payload = workflow_mapper.count_payload(namespace, query, resp)
    return make_tool_result(
        workflow_renderer.count(payload),
        structured_content=structured_content,
        structured=payload,
    )
