"""Task queue and search-attribute MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import task_queue_mapper
from temporal_mcp.providers import TemporalTaskQueueServiceProvider
from temporal_mcp.renderers import task_queue_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.task_queue_service import TemporalTaskQueueService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_tool_result


temporal_task_queue_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.TASK_QUEUE, TemporalToolTags.READ}
ATTR_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.SEARCH_ATTRIBUTE, TemporalToolTags.READ}


@temporal_task_queue_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Task Queue"))
async def describe_task_queue(
    namespace: Namespace,
    task_queue: Annotated[str, Field(description="Task queue name")],
    *,
    structured_content: StructuredContent = False,
    task_queue_service: TemporalTaskQueueService = TemporalTaskQueueServiceProvider,
) -> ToolResult:
    """Get active pollers and reachability for a task queue.

    Args:
        namespace: Target namespace.
        task_queue: Task queue name.
        structured_content: Return structured content for programmatic use.
        task_queue_service: Task queue service (injected).

    Returns:
        ToolResult with poller info as Markdown text and optional structured content.
    """
    payload = task_queue_mapper.task_queue_info(
        namespace,
        task_queue,
        await task_queue_service.describe_task_queue(namespace, task_queue),
    )
    return make_tool_result(
        task_queue_renderer.task_queue(payload),
        structured_content=structured_content,
        structured={"task_queue": payload},
    )


@temporal_task_queue_mcp.tool(tags=ATTR_TAGS, annotations=read_only("List Search Attributes"))
async def list_search_attributes(
    namespace: Namespace,
    *,
    structured_content: StructuredContent = False,
    task_queue_service: TemporalTaskQueueService = TemporalTaskQueueServiceProvider,
) -> ToolResult:
    """List custom and system search attributes available in a namespace.

    Args:
        namespace: Target namespace.
        structured_content: Return structured content for programmatic use.
        task_queue_service: Task queue service (injected).

    Returns:
        ToolResult with the attribute maps as Markdown text and optional structured content.
    """
    payload = task_queue_mapper.search_attributes_info(
        namespace,
        await task_queue_service.list_search_attributes(namespace),
    )
    return make_tool_result(
        task_queue_renderer.search_attributes(payload),
        structured_content=structured_content,
        structured={"search_attributes": payload},
    )
