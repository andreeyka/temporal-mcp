"""Render worker deployment output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import WorkerDeploymentDetail, WorkerDeploymentSummary


_ENTITY_RENDERER = EntityRenderer()
_WORKER_DEPLOYMENT_COLUMNS = ("name", "create_time")
_WORKER_DEPLOYMENT_SPEC = RenderSpec(title="Worker Deployments", columns=_WORKER_DEPLOYMENT_COLUMNS)


def worker_deployment_list(items: list[WorkerDeploymentSummary]) -> str:
    """Render worker deployment summaries as Markdown.

    Args:
        items: Worker deployment summaries to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.list(items, _WORKER_DEPLOYMENT_SPEC)


def worker_deployment_detail(detail: WorkerDeploymentDetail) -> str:
    """Render one worker deployment as Markdown.

    Args:
        detail: Worker deployment detail to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.detail(detail, "Worker Deployment")
