"""Read-only MCP resources exposing Temporal cluster/namespace data."""

from __future__ import annotations

from fastmcp.server.providers import LocalProvider

from temporal_mcp.mappers import failure_mapper, namespace_mapper
from temporal_mcp.providers import TemporalFailureServiceProvider, TemporalNamespaceServiceProvider

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.failure_service import TemporalFailureService  # noqa: TC001
from temporal_mcp.services.namespace_service import TemporalNamespaceService  # noqa: TC001
from temporal_mcp.utils.tool_output import to_json_text


resources_mcp = LocalProvider()


@resources_mcp.resource("temporal://namespaces", mime_type="application/json")
async def namespaces_resource(
    *,
    namespace_service: TemporalNamespaceService = TemporalNamespaceServiceProvider,
) -> str:
    """List all namespaces in the cluster as JSON.

    Args:
        namespace_service: Namespace service (injected).

    Returns:
        JSON text: an array of namespace summaries.
    """
    resp = await namespace_service.list_namespaces()
    items = [namespace_mapper.namespace_summary(n) for n in resp.namespaces]
    return to_json_text(items)


@resources_mcp.resource("temporal://namespace/{ns}/failures", mime_type="application/json")
async def namespace_failures_resource(
    ns: str,
    *,
    failure_service: TemporalFailureService = TemporalFailureServiceProvider,
) -> str:
    """Summarize failures in a namespace as JSON.

    Args:
        ns: Target namespace (from the resource URI).
        failure_service: Failure service (injected).

    Returns:
        JSON text: a FailureSummary for the namespace.
    """
    data = await failure_service.fetch_namespace_failure_data(ns)
    causes = failure_mapper.root_causes_of_histories(data.histories)
    summary = failure_mapper.build_summary(data.namespace, data.since, data.count, causes, data.sample_size)
    return to_json_text(summary)
