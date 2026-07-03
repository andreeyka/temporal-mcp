"""Nexus endpoint operations (cluster-scoped, via operator_service)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from temporalio.api.nexus.v1 import EndpointSpec, EndpointTarget
from temporalio.api.operatorservice.v1 import (
    CreateNexusEndpointRequest,
    DeleteNexusEndpointRequest,
    GetNexusEndpointRequest,
    ListNexusEndpointsRequest,
)


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalNexusService:
    """List, describe, create, and delete cluster-scoped Nexus endpoints.

    Nexus endpoints are cluster-scoped: the operator-service RPCs backing this
    class take no namespace. The `namespace` parameter on every method is used
    only to select/establish the client connection via the per-namespace pool
    (`self._pool.get(namespace)`); it is not sent on the wire.
    """

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_nexus_endpoints(self, namespace: str, page_size: int = 50, name: str = "") -> list[Any]:
        """List Nexus endpoints (single page).

        Args:
            namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
            page_size: Maximum endpoints to return.
            name: Optional exact endpoint name filter.

        Returns:
            A list of nexus.v1.Endpoint protos.
        """
        client = await self._pool.get(namespace)
        resp = await client.operator_service.list_nexus_endpoints(
            ListNexusEndpointsRequest(page_size=page_size, name=name)
        )
        return list(resp.endpoints)

    async def get_nexus_endpoint(self, namespace: str, endpoint_id: str) -> Any:  # noqa: ANN401
        """Return one Nexus endpoint by id.

        Args:
            namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
            endpoint_id: Endpoint id.

        Returns:
            A nexus.v1.Endpoint proto.
        """
        client = await self._pool.get(namespace)
        resp = await client.operator_service.get_nexus_endpoint(GetNexusEndpointRequest(id=endpoint_id))
        return resp.endpoint

    async def create_nexus_endpoint(self, namespace: str, name: str, target_namespace: str, task_queue: str) -> Any:  # noqa: ANN401
        """Create a Nexus endpoint targeting a worker (namespace + task queue).

        Args:
            namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
            name: Endpoint name.
            target_namespace: Namespace of the worker target.
            task_queue: Task queue of the worker target.

        Returns:
            The created nexus.v1.Endpoint proto.
        """
        client = await self._pool.get(namespace)
        spec = EndpointSpec(
            name=name,
            target=EndpointTarget(worker=EndpointTarget.Worker(namespace=target_namespace, task_queue=task_queue)),
        )
        resp = await client.operator_service.create_nexus_endpoint(CreateNexusEndpointRequest(spec=spec))
        return resp.endpoint

    async def delete_nexus_endpoint(self, namespace: str, endpoint_id: str, version: int) -> None:
        """Delete a Nexus endpoint (optimistic concurrency via version).

        Args:
            namespace: Selects the cluster connection; Nexus endpoints are cluster-scoped.
            endpoint_id: Endpoint id to delete.
            version: Current endpoint version, as read from get/list.
        """
        client = await self._pool.get(namespace)
        await client.operator_service.delete_nexus_endpoint(DeleteNexusEndpointRequest(id=endpoint_id, version=version))
