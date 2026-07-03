"""Workflow mutation MCP tools."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.providers import TemporalWorkflowServiceProvider

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.workflow_service import TemporalWorkflowService  # noqa: TC001
from temporal_mcp.tool_annotations import mutating, write
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_action_result


temporal_workflow_mutate_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
WorkflowId = Annotated[str, Field(description="Workflow id")]
RunId = Annotated[str | None, Field(description="Run id (optional)")]
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.WORKFLOW, TemporalToolTags.MUTATING}


@temporal_workflow_mutate_mcp.tool(tags=MUTATE_TAGS, annotations=write("Start Workflow"))
async def start_workflow(
    namespace: Namespace,
    workflow_type: Annotated[str, Field(description="Workflow type name")],
    task_queue: Annotated[str, Field(description="Task queue")],
    workflow_id: WorkflowId,
    args: Annotated[list[Any] | None, Field(description="Positional workflow args")] = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Start a new workflow execution. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_type: Workflow type name.
        task_queue: Task queue.
        workflow_id: Workflow id.
        args: Optional positional arguments.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the new workflow id and run id as Markdown text and optional structured content.
    """
    handle = await workflow_service.start_workflow(namespace, workflow_type, task_queue, workflow_id, args)
    payload = {"workflow_id": handle.id, "run_id": handle.result_run_id}
    return make_action_result(payload, "Workflow Started", structured_content=structured_content)


@temporal_workflow_mutate_mcp.tool(tags=MUTATE_TAGS, annotations=write("Signal Workflow"))
async def signal_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    signal: Annotated[str, Field(description="Signal name")],
    args: Annotated[list[Any] | None, Field(description="Signal args")] = None,
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Send a signal to a running workflow. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        signal: Signal name.
        args: Optional signal arguments.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult confirming the signal as Markdown text and optional structured content.
    """
    await workflow_service.signal_workflow(namespace, workflow_id, signal, args, run_id)
    payload = {"ok": True, "workflow_id": workflow_id, "signal": signal}
    return make_action_result(payload, "Workflow Signaled", structured_content=structured_content)


@temporal_workflow_mutate_mcp.tool(tags=MUTATE_TAGS, annotations=write("Query Workflow"))
async def query_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    query_name: Annotated[str, Field(description="Query handler name")],
    args: Annotated[list[Any] | None, Field(description="Query args")] = None,
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Query workflow state via a registered query handler. (May run user code).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        query_name: Registered query name.
        args: Optional query arguments.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the query result as Markdown text and optional structured content.
    """
    value = await workflow_service.query_workflow(namespace, workflow_id, query_name, args, run_id)
    payload = {"workflow_id": workflow_id, "query": query_name, "result": value}
    return make_action_result(payload, "Workflow Query Result", structured_content=structured_content)


@temporal_workflow_mutate_mcp.tool(tags=MUTATE_TAGS, annotations=write("Cancel Workflow"))
async def cancel_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Request graceful cancellation. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult confirming the cancellation request as Markdown text and optional structured content.
    """
    await workflow_service.cancel_workflow(namespace, workflow_id, run_id)
    payload = {"ok": True, "workflow_id": workflow_id}
    return make_action_result(payload, "Workflow Cancel Requested", structured_content=structured_content)


@temporal_workflow_mutate_mcp.tool(tags=MUTATE_TAGS, annotations=mutating("Terminate Workflow"))
async def terminate_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    reason: Annotated[str, Field(description="Termination reason")] = "",
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Force-terminate a workflow immediately, no cleanup. (Mutating, destructive).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        reason: Termination reason.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult confirming the termination as Markdown text and optional structured content.
    """
    await workflow_service.terminate_workflow(namespace, workflow_id, reason, run_id)
    payload = {"ok": True, "workflow_id": workflow_id, "reason": reason}
    return make_action_result(payload, "Workflow Terminated", structured_content=structured_content)
