"""Cluster and namespace read operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from temporalio.api.workflowservice.v1 import DescribeNamespaceRequest, GetSystemInfoRequest, ListNamespacesRequest


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalNamespaceService:
    """Cluster-scoped and namespace-scoped read operations."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def get_cluster_info(self) -> Any:  # noqa: ANN401
        """Return server version and capabilities."""
        client = await self._pool.bootstrap()
        return await client.workflow_service.get_system_info(GetSystemInfoRequest())

    async def list_namespaces(self, page_size: int = 100) -> Any:  # noqa: ANN401
        """Return all namespaces in the cluster."""
        client = await self._pool.bootstrap()
        return await client.workflow_service.list_namespaces(ListNamespacesRequest(page_size=page_size))

    async def describe_namespace(self, namespace: str) -> Any:  # noqa: ANN401
        """Return config/retention/replication info for one namespace."""
        client = await self._pool.bootstrap()
        return await client.workflow_service.describe_namespace(DescribeNamespaceRequest(namespace=namespace))
