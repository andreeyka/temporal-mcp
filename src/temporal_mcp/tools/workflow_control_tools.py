"""Workflow lifecycle-control MCP tools (pause/unpause/signal-with-start/update/reset)."""

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


temporal_workflow_control_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
WorkflowId = Annotated[str, Field(description="Workflow id")]
RunId = Annotated[str | None, Field(description="Run id (optional)")]
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.WORKFLOW, TemporalToolTags.MUTATING}


@temporal_workflow_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Pause Workflow"))
async def pause_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    reason: Annotated[str, Field(description="Reason for pausing")] = "",
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Pause a running workflow, stopping new workflow-task scheduling. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        reason: Reason for pausing.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult confirming the pause as Markdown text and optional structured content.
    """
    await workflow_service.pause_workflow(namespace, workflow_id, reason, run_id)
    payload = {"ok": True, "workflow_id": workflow_id}
    return make_action_result(payload, "Workflow Paused", structured_content=structured_content)


@temporal_workflow_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Unpause Workflow"))
async def unpause_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    reason: Annotated[str, Field(description="Reason for unpausing")] = "",
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Resume a paused workflow. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        reason: Reason for unpausing.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult confirming the resume as Markdown text and optional structured content.
    """
    await workflow_service.unpause_workflow(namespace, workflow_id, reason, run_id)
    payload = {"ok": True, "workflow_id": workflow_id}
    return make_action_result(payload, "Workflow Unpaused", structured_content=structured_content)


@temporal_workflow_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Signal With Start Workflow"))
async def signal_with_start_workflow(
    namespace: Namespace,
    workflow_type: Annotated[str, Field(description="Workflow type name")],
    task_queue: Annotated[str, Field(description="Task queue")],
    workflow_id: WorkflowId,
    signal: Annotated[str, Field(description="Signal name")],
    signal_args: Annotated[list[Any] | None, Field(description="Signal args")] = None,
    args: Annotated[list[Any] | None, Field(description="Positional workflow args")] = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Start a workflow and deliver a signal atomically, or signal it if already running. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_type: Workflow type name.
        task_queue: Task queue.
        workflow_id: Workflow id.
        signal: Signal name.
        signal_args: Optional signal arguments.
        args: Optional positional workflow arguments.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the workflow id and run id as Markdown text and optional structured content.
    """
    handle = await workflow_service.signal_with_start_workflow(
        namespace, workflow_type, task_queue, workflow_id, signal, signal_args, args
    )
    payload = {"workflow_id": handle.id, "run_id": handle.result_run_id}
    return make_action_result(payload, "Workflow Signaled/Started", structured_content=structured_content)


@temporal_workflow_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Update Workflow"))
async def update_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    update: Annotated[str, Field(description="Update handler name")],
    args: Annotated[list[Any] | None, Field(description="Update args")] = None,
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Send an update to a running workflow and wait for its result. (Mutating).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        update: Update handler name.
        args: Optional update arguments.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the update result as Markdown text and optional structured content.
    """
    value = await workflow_service.update_workflow(namespace, workflow_id, update, args, run_id)
    payload = {"workflow_id": workflow_id, "update": update, "result": value}
    return make_action_result(payload, "Workflow Updated", structured_content=structured_content)


@temporal_workflow_control_mcp.tool(tags=MUTATE_TAGS, annotations=mutating("Reset Workflow"))
async def reset_workflow(
    namespace: Namespace,
    workflow_id: WorkflowId,
    event_id: Annotated[int, Field(description="workflow_task_finish_event_id to reset to", ge=1)],
    reason: Annotated[str, Field(description="Reason for the reset")] = "",
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    workflow_service: TemporalWorkflowService = TemporalWorkflowServiceProvider,
) -> ToolResult:
    """Reset a workflow to a prior history event, abandoning the current run and creating a new one. (Destructive).

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id.
        event_id: The workflow_task_finish_event_id to reset to (no implicit reset-to-start).
        reason: Reason for the reset.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        workflow_service: Workflow service (injected).

    Returns:
        ToolResult with the new run id as Markdown text and optional structured content.
    """
    resp = await workflow_service.reset_workflow(namespace, workflow_id, event_id, reason, run_id)
    payload = {"ok": True, "workflow_id": workflow_id, "new_run_id": resp.run_id}
    return make_action_result(payload, "Workflow Reset", structured_content=structured_content)
