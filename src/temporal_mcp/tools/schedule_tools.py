"""Schedule MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import schedule_mapper
from temporal_mcp.providers import TemporalScheduleServiceProvider
from temporal_mcp.renderers import schedule_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.schedule_service import TemporalScheduleService  # noqa: TC001
from temporal_mcp.tool_annotations import mutating, read_only, write
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_action_result, make_tool_result


temporal_schedule_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
ScheduleId = Annotated[str, Field(description="Schedule id")]
Note = Annotated[str, Field(description="Optional note")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.SCHEDULE, TemporalToolTags.READ}
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.SCHEDULE, TemporalToolTags.MUTATING}


@temporal_schedule_mcp.tool(tags=READ_TAGS, annotations=read_only("List Schedules"))
async def list_schedules(
    namespace: Namespace,
    limit: Annotated[int, Field(description="Max schedules", ge=1, le=1000)] = 50,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """List schedules in a namespace.

    Args:
        namespace: Target namespace.
        limit: Maximum number of schedules.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult with the schedule list as Markdown text and optional structured content.
    """
    payload = schedule_mapper.schedule_list(namespace, await schedule_service.list_schedules(namespace, limit))
    return make_tool_result(
        schedule_renderer.schedule_list(payload),
        structured_content=structured_content,
        structured=payload,
    )


@temporal_schedule_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Schedule"))
async def describe_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Get spec, state, and next run times for a schedule.

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult with schedule detail as Markdown text and optional structured content.
    """
    description = await schedule_service.describe_schedule(namespace, schedule_id)
    detail = schedule_mapper.schedule_detail(schedule_id, description)
    return make_tool_result(
        schedule_renderer.schedule_detail(detail),
        structured_content=structured_content,
        structured={"schedule": detail},
    )


@temporal_schedule_mcp.tool(tags=MUTATE_TAGS, annotations=write("Pause Schedule"))
async def pause_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    note: Note = "",
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Pause a schedule. (Mutating).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id.
        note: Optional note.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming the pause as Markdown text and optional structured content.
    """
    await schedule_service.pause_schedule(namespace, schedule_id, note)
    payload = {"ok": True, "schedule_id": schedule_id}
    return make_action_result(payload, "Schedule Paused", structured_content=structured_content)


@temporal_schedule_mcp.tool(tags=MUTATE_TAGS, annotations=write("Unpause Schedule"))
async def unpause_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    note: Note = "",
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Resume a paused schedule. (Mutating).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id.
        note: Optional note.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming the resume as Markdown text and optional structured content.
    """
    await schedule_service.unpause_schedule(namespace, schedule_id, note)
    payload = {"ok": True, "schedule_id": schedule_id}
    return make_action_result(payload, "Schedule Unpaused", structured_content=structured_content)


@temporal_schedule_mcp.tool(tags=MUTATE_TAGS, annotations=mutating("Delete Schedule"))
async def delete_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Delete a schedule. (Mutating, destructive).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming the deletion as Markdown text and optional structured content.
    """
    await schedule_service.delete_schedule(namespace, schedule_id)
    payload = {"ok": True, "schedule_id": schedule_id}
    return make_action_result(payload, "Schedule Deleted", structured_content=structured_content)
