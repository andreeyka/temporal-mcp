"""Activity read MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import activity_mapper
from temporal_mcp.providers import TemporalActivityServiceProvider
from temporal_mcp.renderers import activity_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.activity_service import TemporalActivityService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_tool_result


temporal_activity_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.ACTIVITY, TemporalToolTags.READ}


@temporal_activity_mcp.tool(tags=READ_TAGS, annotations=read_only("List Activities"))
async def list_activities(
    namespace: Namespace,
    query: Annotated[str | None, Field(description='Visibility query, e.g. ActivityType="Foo"')] = None,
    limit: Annotated[int, Field(description="Max activities", ge=1, le=1000)] = 50,
    *,
    structured_content: StructuredContent = False,
    activity_service: TemporalActivityService = TemporalActivityServiceProvider,
) -> ToolResult:
    """List activity executions in a namespace, optionally filtered by a visibility query.

    Args:
        namespace: Target namespace.
        query: Optional visibility query.
        limit: Maximum number of activities.
        structured_content: Return structured content for programmatic use.
        activity_service: Activity service (injected).

    Returns:
        ToolResult with the activity list as Markdown text and optional structured content.
    """
    items = activity_mapper.activity_summaries(
        await activity_service.list_activities(namespace, query=query, limit=limit)
    )
    return make_tool_result(
        activity_renderer.activity_list(items),
        structured_content=structured_content,
        structured={"activities": items},
    )


@temporal_activity_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Activity"))
async def describe_activity(
    namespace: Namespace,
    activity_id: Annotated[str, Field(description="Activity id")],
    run_id: Annotated[str | None, Field(description="Activity run id (optional)")] = None,
    *,
    structured_content: StructuredContent = False,
    activity_service: TemporalActivityService = TemporalActivityServiceProvider,
) -> ToolResult:
    """Get state, attempt count, heartbeat, and failure details for one activity execution.

    Args:
        namespace: Target namespace.
        activity_id: Activity id.
        run_id: Optional activity run id.
        structured_content: Return structured content for programmatic use.
        activity_service: Activity service (injected).

    Returns:
        ToolResult with the activity detail as Markdown text and optional structured content.
    """
    detail = activity_mapper.activity_detail(await activity_service.describe_activity(namespace, activity_id, run_id))
    return make_tool_result(
        activity_renderer.activity_detail(detail),
        structured_content=structured_content,
        structured={"activity": detail},
    )
