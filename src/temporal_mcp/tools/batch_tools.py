"""Batch-operations MCP tools (list/describe reads, stop write)."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import batch_mapper
from temporal_mcp.providers import TemporalBatchServiceProvider
from temporal_mcp.renderers import batch_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.batch_service import TemporalBatchService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only, write
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_action_result, make_tool_result


temporal_batch_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
JobId = Annotated[str, Field(description="Batch job id")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.BATCH, TemporalToolTags.READ}
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.BATCH, TemporalToolTags.MUTATING}


@temporal_batch_mcp.tool(tags=READ_TAGS, annotations=read_only("List Batch Operations"))
async def list_batch_operations(
    namespace: Namespace,
    page_size: Annotated[int, Field(description="Max operations", ge=1, le=1000)] = 50,
    *,
    structured_content: StructuredContent = False,
    batch_service: TemporalBatchService = TemporalBatchServiceProvider,
) -> ToolResult:
    """List batch operations in a namespace.

    Args:
        namespace: Target namespace.
        page_size: Maximum number of operations.
        structured_content: Return structured content for programmatic use.
        batch_service: Batch service (injected).

    Returns:
        ToolResult with the batch operation list as Markdown text and optional structured content.
    """
    items = batch_mapper.batch_operation_summaries(await batch_service.list_batch_operations(namespace, page_size))
    return make_tool_result(
        batch_renderer.batch_operation_list(items),
        structured_content=structured_content,
        structured={"batch_operations": items},
    )


@temporal_batch_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Batch Operation"))
async def describe_batch_operation(
    namespace: Namespace,
    job_id: JobId,
    *,
    structured_content: StructuredContent = False,
    batch_service: TemporalBatchService = TemporalBatchServiceProvider,
) -> ToolResult:
    """Get progress and status detail for one batch operation job.

    Args:
        namespace: Target namespace.
        job_id: Batch job id.
        structured_content: Return structured content for programmatic use.
        batch_service: Batch service (injected).

    Returns:
        ToolResult with the batch operation detail as Markdown text and optional structured content.
    """
    detail = batch_mapper.batch_operation_detail(await batch_service.describe_batch_operation(namespace, job_id))
    return make_tool_result(
        batch_renderer.batch_operation_detail(detail),
        structured_content=structured_content,
        structured={"batch_operation": detail},
    )


@temporal_batch_mcp.tool(tags=MUTATE_TAGS, annotations=write("Stop Batch Operation"))
async def stop_batch_operation(
    namespace: Namespace,
    job_id: JobId,
    reason: Annotated[str, Field(description="Reason for stopping the batch job")],
    identity: Annotated[str, Field(description="Caller identity recorded on the batch job")] = "temporal-mcp",
    *,
    structured_content: StructuredContent = False,
    batch_service: TemporalBatchService = TemporalBatchServiceProvider,
) -> ToolResult:
    """Stop a running batch operation. (Mutating).

    Args:
        namespace: Target namespace.
        job_id: Batch job id.
        reason: Reason for stopping the batch job.
        identity: Caller identity recorded on the batch job.
        structured_content: Return structured content for programmatic use.
        batch_service: Batch service (injected).

    Returns:
        ToolResult confirming the stop as Markdown text and optional structured content.
    """
    await batch_service.stop_batch_operation(namespace, job_id, reason, identity)
    payload = {"job_id": job_id, "stopped": True}
    return make_action_result(payload, "Batch Operation Stopped", structured_content=structured_content)
