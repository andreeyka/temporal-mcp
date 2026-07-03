"""Failure-analysis MCP tools (read-only)."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import failure_mapper
from temporal_mcp.providers import TemporalFailureServiceProvider
from temporal_mcp.renderers import failure_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.failure_service import TemporalFailureService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_tool_result


temporal_failure_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
WorkflowId = Annotated[str, Field(description="Workflow id")]
RunId = Annotated[str | None, Field(description="Run id (optional)")]
Since = Annotated[
    str | None,
    Field(
        default=None,
        description='Lower bound on StartTime, ISO-8601, e.g. "2026-01-01T00:00:00Z"',
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
    ),
]
SampleSize = Annotated[int, Field(description="Max failed workflows to sample for error-type breakdown", ge=1, le=1000)]
Limit = Annotated[int, Field(description="Max ranked failure groups", ge=1, le=100)]
READ_TAGS: set[str] = {
    TemporalToolTags.TEMPORAL,
    TemporalToolTags.WORKFLOW,
    TemporalToolTags.FAILURE,
    TemporalToolTags.READ,
}


@temporal_failure_mcp.tool(tags=READ_TAGS, annotations=read_only("Analyze Workflow Failure"))
async def analyze_workflow_failure(
    namespace: Namespace,
    workflow_id: WorkflowId,
    run_id: RunId = None,
    *,
    structured_content: StructuredContent = False,
    failure_service: TemporalFailureService = TemporalFailureServiceProvider,
) -> ToolResult:
    """Analyze a workflow's terminal failure, unwrapping the full cause chain.

    Args:
        namespace: Target namespace.
        workflow_id: Workflow id to analyze.
        run_id: Optional run id.
        structured_content: Return structured content for programmatic use.
        failure_service: Failure service (injected).

    Returns:
        ToolResult with the analysis as Markdown text and optional structured content.
    """
    data = await failure_service.fetch_workflow_failure_data(namespace, workflow_id, run_id)
    analysis = failure_mapper.build_analysis(
        data.namespace,
        data.workflow_id,
        data.run_id,
        data.description,
        data.history,
    )
    return make_tool_result(
        failure_renderer.failure_analysis(analysis),
        structured_content=structured_content,
        structured={"analysis": analysis},
    )


@temporal_failure_mcp.tool(tags=READ_TAGS, annotations=read_only("Summarize Namespace Failures"))
async def summarize_namespace_failures(
    namespace: Namespace,
    since: Since = None,
    sample_size: SampleSize = 100,
    *,
    structured_content: StructuredContent = False,
    failure_service: TemporalFailureService = TemporalFailureServiceProvider,
) -> ToolResult:
    """Summarize namespace failures: exact counts by type + sampled error types.

    Args:
        namespace: Target namespace.
        since: Optional ISO-8601 lower bound on StartTime.
        sample_size: Max failed workflows to sample.
        structured_content: Return structured content for programmatic use.
        failure_service: Failure service (injected).

    Returns:
        ToolResult with the summary as Markdown text and optional structured content.
    """
    data = await failure_service.fetch_namespace_failure_data(namespace, since, sample_size)
    causes = failure_mapper.root_causes_of_histories(data.histories)
    summary = failure_mapper.build_summary(data.namespace, data.since, data.count, causes, data.sample_size)
    return make_tool_result(
        failure_renderer.failure_summary(summary),
        structured_content=structured_content,
        structured={"summary": summary},
    )


@temporal_failure_mcp.tool(tags=READ_TAGS, annotations=read_only("Top Failure Types"))
async def top_failure_types(
    namespace: Namespace,
    limit: Limit = 10,
    since: Since = None,
    sample_size: SampleSize = 100,
    *,
    structured_content: StructuredContent = False,
    failure_service: TemporalFailureService = TemporalFailureServiceProvider,
) -> ToolResult:
    """Rank the top failure categories from a bounded sample of failed workflows.

    Args:
        namespace: Target namespace.
        limit: Max ranked groups to return.
        since: Optional ISO-8601 lower bound on StartTime.
        sample_size: Max failed workflows to sample.
        structured_content: Return structured content for programmatic use.
        failure_service: Failure service (injected).

    Returns:
        ToolResult with ranked groups as Markdown text and optional structured content.
    """
    histories = await failure_service.fetch_failure_histories(namespace, since, sample_size)
    causes = failure_mapper.root_causes_of_histories(histories)
    groups = failure_mapper.top_groups(causes, limit)
    return make_tool_result(
        failure_renderer.failure_groups(groups),
        structured_content=structured_content,
        structured={"groups": groups},
    )
