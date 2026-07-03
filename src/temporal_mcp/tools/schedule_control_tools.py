"""Schedule create/update/trigger/backfill MCP tools."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.providers import TemporalScheduleServiceProvider

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.schedule_service import TemporalScheduleService  # noqa: TC001
from temporal_mcp.tool_annotations import write
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_action_result


temporal_schedule_control_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
ScheduleId = Annotated[str, Field(description="Schedule id")]
Cron = Annotated[str | None, Field(description="Cron expression, e.g. '0 * * * *'")]
IntervalSeconds = Annotated[int | None, Field(description="Interval between runs, in seconds", ge=1)]
Overlap = Annotated[
    Literal["SKIP", "BUFFER_ONE", "BUFFER_ALL", "ALLOW_ALL", "CANCEL_OTHER", "TERMINATE_OTHER"] | None,
    Field(description="Overlap policy for concurrent runs"),
]
IsoTime = Annotated[
    str,
    Field(
        description='ISO-8601 timestamp, e.g. "2026-01-01T00:00:00Z"',
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
    ),
]
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.SCHEDULE, TemporalToolTags.MUTATING}


@temporal_schedule_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Create Schedule"))
async def create_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    workflow_type: Annotated[str, Field(description="Workflow type name to start")],
    task_queue: Annotated[str, Field(description="Task queue")],
    workflow_id: Annotated[str, Field(description="Workflow id for scheduled runs")],
    cron: Cron = None,
    interval_seconds: IntervalSeconds = None,
    args: Annotated[list[Any] | None, Field(description="Positional workflow args")] = None,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Create a cron- or interval-based schedule that starts a workflow. (Mutating).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id to create.
        workflow_type: Workflow type name to start.
        task_queue: Task queue.
        workflow_id: Workflow id used for scheduled runs.
        cron: Cron expression (provide this or interval_seconds).
        interval_seconds: Interval between runs in seconds (provide this or cron).
        args: Optional positional workflow arguments.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming creation as Markdown text and optional structured content.

    Raises:
        InvalidScheduleSpecError: If neither, or both, cron and interval_seconds are given.
    """
    await schedule_service.create_schedule(
        namespace, schedule_id, workflow_type, task_queue, workflow_id, cron, interval_seconds, args
    )
    payload = {"ok": True, "schedule_id": schedule_id}
    return make_action_result(payload, "Schedule Created", structured_content=structured_content)


@temporal_schedule_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Update Schedule"))
async def update_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    cron: Cron = None,
    interval_seconds: IntervalSeconds = None,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Replace a schedule's spec with a new cron/interval spec. (Mutating).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id to update.
        cron: New cron expression (provide this or interval_seconds).
        interval_seconds: New interval between runs in seconds (provide this or cron).
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming the update as Markdown text and optional structured content.

    Raises:
        InvalidScheduleSpecError: If neither, or both, cron and interval_seconds are given.
    """
    await schedule_service.update_schedule(namespace, schedule_id, cron, interval_seconds)
    payload = {"ok": True, "schedule_id": schedule_id}
    return make_action_result(payload, "Schedule Updated", structured_content=structured_content)


@temporal_schedule_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Trigger Schedule"))
async def trigger_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    overlap: Overlap = None,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Trigger a schedule action immediately, once. (Mutating).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id to trigger.
        overlap: Optional overlap policy for the triggered run.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming the trigger as Markdown text and optional structured content.
    """
    await schedule_service.trigger_schedule(namespace, schedule_id, overlap)
    payload = {"ok": True, "schedule_id": schedule_id}
    return make_action_result(payload, "Schedule Triggered", structured_content=structured_content)


@temporal_schedule_control_mcp.tool(tags=MUTATE_TAGS, annotations=write("Backfill Schedule"))
async def backfill_schedule(
    namespace: Namespace,
    schedule_id: ScheduleId,
    start_time: IsoTime,
    end_time: IsoTime,
    overlap: Overlap = None,
    *,
    structured_content: StructuredContent = False,
    schedule_service: TemporalScheduleService = TemporalScheduleServiceProvider,
) -> ToolResult:
    """Backfill a schedule over a past ISO-8601 time range. (Mutating).

    Args:
        namespace: Target namespace.
        schedule_id: Schedule id to backfill.
        start_time: ISO-8601 range start.
        end_time: ISO-8601 range end.
        overlap: Optional overlap policy for backfilled runs.
        structured_content: Return structured content for programmatic use.
        schedule_service: Schedule service (injected).

    Returns:
        ToolResult confirming the backfill as Markdown text and optional structured content.
    """
    await schedule_service.backfill_schedule(namespace, schedule_id, start_time, end_time, overlap)
    payload = {"ok": True, "schedule_id": schedule_id, "start_time": start_time, "end_time": end_time}
    return make_action_result(payload, "Schedule Backfill Started", structured_content=structured_content)
