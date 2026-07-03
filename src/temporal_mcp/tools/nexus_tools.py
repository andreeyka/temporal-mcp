"""Nexus endpoint MCP tools (cluster-scoped, via operator_service)."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import nexus_mapper
from temporal_mcp.providers import TemporalNexusServiceProvider
from temporal_mcp.renderers import nexus_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.nexus_service import TemporalNexusService  # noqa: TC001
from temporal_mcp.tool_annotations import mutating, read_only, write
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_action_result, make_tool_result


temporal_nexus_mcp = LocalProvider()

Namespace = Annotated[
    str, Field(description="Namespace selecting the cluster connection (Nexus endpoints are cluster-scoped)")
]
EndpointId = Annotated[str, Field(description="Nexus endpoint id")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.NEXUS, TemporalToolTags.READ}
MUTATE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.NEXUS, TemporalToolTags.MUTATING}


@temporal_nexus_mcp.tool(tags=READ_TAGS, annotations=read_only("List Nexus Endpoints"))
async def list_nexus_endpoints(
    namespace: Namespace,
    page_size: Annotated[int, Field(description="Max endpoints", ge=1, le=1000)] = 50,
    name: Annotated[str, Field(description="Optional exact endpoint name filter")] = "",
    *,
    structured_content: StructuredContent = False,
    nexus_service: TemporalNexusService = TemporalNexusServiceProvider,
) -> ToolResult:
    """List cluster-scoped Nexus endpoints.

    Args:
        namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
        page_size: Maximum number of endpoints.
        name: Optional exact endpoint name filter.
        structured_content: Return structured content for programmatic use.
        nexus_service: Nexus service (injected).

    Returns:
        ToolResult with the endpoint list as Markdown text and optional structured content.
    """
    items = nexus_mapper.nexus_endpoint_summaries(await nexus_service.list_nexus_endpoints(namespace, page_size, name))
    return make_tool_result(
        nexus_renderer.nexus_endpoint_list(items),
        structured_content=structured_content,
        structured={"nexus_endpoints": items},
    )


@temporal_nexus_mcp.tool(tags=READ_TAGS, annotations=read_only("Get Nexus Endpoint"))
async def get_nexus_endpoint(
    namespace: Namespace,
    endpoint_id: EndpointId,
    *,
    structured_content: StructuredContent = False,
    nexus_service: TemporalNexusService = TemporalNexusServiceProvider,
) -> ToolResult:
    """Get details and target for one Nexus endpoint.

    Args:
        namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
        endpoint_id: Endpoint id.
        structured_content: Return structured content for programmatic use.
        nexus_service: Nexus service (injected).

    Returns:
        ToolResult with the endpoint detail as Markdown text and optional structured content.
    """
    detail = nexus_mapper.nexus_endpoint_detail(await nexus_service.get_nexus_endpoint(namespace, endpoint_id))
    return make_tool_result(
        nexus_renderer.nexus_endpoint_detail(detail),
        structured_content=structured_content,
        structured={"nexus_endpoint": detail},
    )


@temporal_nexus_mcp.tool(tags=MUTATE_TAGS, annotations=write("Create Nexus Endpoint"))
async def create_nexus_endpoint(
    namespace: Namespace,
    name: Annotated[str, Field(description="Endpoint name")],
    target_namespace: Annotated[str, Field(description="Namespace of the worker target")],
    task_queue: Annotated[str, Field(description="Task queue of the worker target")],
    *,
    structured_content: StructuredContent = False,
    nexus_service: TemporalNexusService = TemporalNexusServiceProvider,
) -> ToolResult:
    """Create a Nexus endpoint targeting a worker (namespace + task queue). (Mutating).

    Args:
        namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
        name: Endpoint name.
        target_namespace: Namespace of the worker target.
        task_queue: Task queue of the worker target.
        structured_content: Return structured content for programmatic use.
        nexus_service: Nexus service (injected).

    Returns:
        ToolResult with the created endpoint detail as Markdown text and optional structured content.
    """
    detail = nexus_mapper.nexus_endpoint_detail(
        await nexus_service.create_nexus_endpoint(namespace, name, target_namespace, task_queue)
    )
    return make_tool_result(
        nexus_renderer.nexus_endpoint_detail(detail),
        structured_content=structured_content,
        structured={"nexus_endpoint": detail},
    )


@temporal_nexus_mcp.tool(tags=MUTATE_TAGS, annotations=mutating("Delete Nexus Endpoint"))
async def delete_nexus_endpoint(
    namespace: Namespace,
    endpoint_id: EndpointId,
    version: Annotated[int, Field(description="Current endpoint version, for optimistic concurrency", ge=1)],
    *,
    structured_content: StructuredContent = False,
    nexus_service: TemporalNexusService = TemporalNexusServiceProvider,
) -> ToolResult:
    """Delete a Nexus endpoint. (Destructive).

    Args:
        namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
        endpoint_id: Endpoint id to delete.
        version: Current endpoint version, as read from get/list.
        structured_content: Return structured content for programmatic use.
        nexus_service: Nexus service (injected).

    Returns:
        ToolResult confirming the deletion as Markdown text and optional structured content.
    """
    await nexus_service.delete_nexus_endpoint(namespace, endpoint_id, version)
    payload = {"endpoint_id": endpoint_id, "deleted": True}
    return make_action_result(payload, "Nexus Endpoint Deleted", structured_content=structured_content)
