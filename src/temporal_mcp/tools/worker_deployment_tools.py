"""Worker-deployment read MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from fastmcp.tools import ToolResult  # noqa: TC002
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags
from temporal_mcp.mappers import worker_deployment_mapper
from temporal_mcp.providers import TemporalWorkerDeploymentServiceProvider
from temporal_mcp.renderers import worker_deployment_renderer

# Runtime imports (not TYPE_CHECKING): FastMCP resolves tool annotations via
# get_type_hints() to decide output schemas; unresolvable names break the
# ToolResult suppression and every tool wrongly advertises an outputSchema.
from temporal_mcp.services.worker_deployment_service import TemporalWorkerDeploymentService  # noqa: TC001
from temporal_mcp.tool_annotations import read_only
from temporal_mcp.tools.params import StructuredContent  # noqa: TC001
from temporal_mcp.utils.tool_output import make_tool_result


temporal_worker_deployment_mcp = LocalProvider()

Namespace = Annotated[str, Field(description="Namespace name")]
READ_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.WORKER_DEPLOYMENT, TemporalToolTags.READ}


@temporal_worker_deployment_mcp.tool(tags=READ_TAGS, annotations=read_only("List Worker Deployments"))
async def list_worker_deployments(
    namespace: Namespace,
    page_size: Annotated[int, Field(description="Max deployments", ge=1, le=1000)] = 50,
    *,
    structured_content: StructuredContent = False,
    worker_deployment_service: TemporalWorkerDeploymentService = TemporalWorkerDeploymentServiceProvider,
) -> ToolResult:
    """List versioned worker deployments in a namespace.

    Args:
        namespace: Target namespace.
        page_size: Maximum number of deployments.
        structured_content: Return structured content for programmatic use.
        worker_deployment_service: Worker-deployment service (injected).

    Returns:
        ToolResult with the deployment list as Markdown text and optional structured content.
    """
    items = worker_deployment_mapper.worker_deployment_summaries(
        await worker_deployment_service.list_worker_deployments(namespace, page_size)
    )
    return make_tool_result(
        worker_deployment_renderer.worker_deployment_list(items),
        structured_content=structured_content,
        structured={"worker_deployments": items},
    )


@temporal_worker_deployment_mcp.tool(tags=READ_TAGS, annotations=read_only("Describe Worker Deployment"))
async def describe_worker_deployment(
    namespace: Namespace,
    deployment_name: Annotated[str, Field(description="Worker deployment name")],
    *,
    structured_content: StructuredContent = False,
    worker_deployment_service: TemporalWorkerDeploymentService = TemporalWorkerDeploymentServiceProvider,
) -> ToolResult:
    """Get current/ramping version and metadata for one worker deployment.

    Args:
        namespace: Target namespace.
        deployment_name: Worker deployment name.
        structured_content: Return structured content for programmatic use.
        worker_deployment_service: Worker-deployment service (injected).

    Returns:
        ToolResult with the deployment detail as Markdown text and optional structured content.
    """
    detail = worker_deployment_mapper.worker_deployment_detail(
        await worker_deployment_service.describe_worker_deployment(namespace, deployment_name)
    )
    return make_tool_result(
        worker_deployment_renderer.worker_deployment_detail(detail),
        structured_content=structured_content,
        structured={"worker_deployment": detail},
    )
