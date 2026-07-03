"""Cluster and namespace MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import namespace_mapper, workflow_mapper
from temporal_mcp.providers import TemporalNamespaceServiceProvider
from temporal_mcp.renderers import namespace_renderer, workflow_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.namespace_service import TemporalNamespaceService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_tool_result


temporal_namespace_mcp = LocalProvider()


@temporal_namespace_mcp.tool(
    tags={TemporalToolTags.TEMPORAL, TemporalToolTags.CLUSTER, TemporalToolTags.READ},
    annotations=read_only("Get Cluster Info"),
)
async def get_cluster_info(
    *,
    structured_content: StructuredContent = False,
    namespace_service: TemporalNamespaceService = TemporalNamespaceServiceProvider,
) -> ToolResult:
    """Get server version, cluster id, and enabled capabilities.

    Args:
        structured_content: Return structured content for programmatic use.
        namespace_service: Namespace service (injected).

    Returns:
        ToolResult with cluster info as Markdown text and optional structured content.
    """
    info = workflow_mapper.cluster_info(await namespace_service.get_cluster_info())
    return make_tool_result(
        workflow_renderer.cluster_info(info),
        structured_content=structured_content,
        structured=info.model_dump(),
    )


@temporal_namespace_mcp.tool(
    tags={TemporalToolTags.TEMPORAL, TemporalToolTags.NAMESPACE, TemporalToolTags.READ},
    annotations=read_only("List Namespaces"),
)
async def list_namespaces(
    page_size: Annotated[int, Field(description="Max namespaces to return", ge=1, le=1000)] = 100,
    *,
    structured_content: StructuredContent = False,
    namespace_service: TemporalNamespaceService = TemporalNamespaceServiceProvider,
) -> ToolResult:
    """List all namespaces in the cluster (use this to discover namespaces).

    Args:
        page_size: Maximum number of namespaces to return.
        structured_content: Return structured content for programmatic use.
        namespace_service: Namespace service (injected).

    Returns:
        ToolResult with the namespace list as Markdown text and optional structured content.
    """
    resp = await namespace_service.list_namespaces(page_size)
    items = [namespace_mapper.namespace_summary(n) for n in resp.namespaces]
    return make_tool_result(
        namespace_renderer.namespace_list(items),
        structured_content=structured_content,
        structured={"namespaces": items},
    )


@temporal_namespace_mcp.tool(
    tags={TemporalToolTags.TEMPORAL, TemporalToolTags.NAMESPACE, TemporalToolTags.READ},
    annotations=read_only("Describe Namespace"),
)
async def describe_namespace(
    namespace: Annotated[str, Field(description="Namespace name")],
    *,
    structured_content: StructuredContent = False,
    namespace_service: TemporalNamespaceService = TemporalNamespaceServiceProvider,
) -> ToolResult:
    """Get config, retention period, and replication info for one namespace.

    Args:
        namespace: Namespace name.
        structured_content: Return structured content for programmatic use.
        namespace_service: Namespace service (injected).

    Returns:
        ToolResult with namespace detail as Markdown text and optional structured content.
    """
    detail = namespace_mapper.namespace_detail(await namespace_service.describe_namespace(namespace))
    return make_tool_result(
        namespace_renderer.namespace_detail(detail),
        structured_content=structured_content,
        structured=detail.model_dump(),
    )
