"""Worker-deployment read operations (low-level workflow_service RPCs)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from temporalio.api.workflowservice.v1 import DescribeWorkerDeploymentRequest, ListWorkerDeploymentsRequest


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalWorkerDeploymentService:
    """List and describe versioned worker deployments."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_worker_deployments(self, namespace: str, page_size: int = 50) -> list[Any]:
        """List worker deployments in a namespace (single page).

        Args:
            namespace: Target namespace.
            page_size: Maximum deployments to return.

        Returns:
            A list of WorkerDeploymentSummary protos.
        """
        client = await self._pool.get(namespace)
        resp = await client.workflow_service.list_worker_deployments(
            ListWorkerDeploymentsRequest(namespace=namespace, page_size=page_size)
        )
        return list(resp.worker_deployments)

    async def describe_worker_deployment(self, namespace: str, deployment_name: str) -> Any:  # noqa: ANN401
        """Return the WorkerDeploymentInfo for one deployment."""
        client = await self._pool.get(namespace)
        resp = await client.workflow_service.describe_worker_deployment(
            DescribeWorkerDeploymentRequest(namespace=namespace, deployment_name=deployment_name)
        )
        return resp.worker_deployment_info
