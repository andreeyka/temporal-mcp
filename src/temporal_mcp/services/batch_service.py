"""Batch-operation read/control operations (low-level workflow_service RPCs)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from temporalio.api.workflowservice.v1 import (
    DescribeBatchOperationRequest,
    ListBatchOperationsRequest,
    StopBatchOperationRequest,
)


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalBatchService:
    """List, describe, and stop batch operations."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_batch_operations(self, namespace: str, page_size: int = 50) -> list[Any]:
        """List batch operations in a namespace (single page).

        Args:
            namespace: Target namespace.
            page_size: Maximum operations to return.

        Returns:
            A list of BatchOperationInfo protos.
        """
        client = await self._pool.get(namespace)
        resp = await client.workflow_service.list_batch_operations(
            ListBatchOperationsRequest(namespace=namespace, page_size=page_size)
        )
        return list(resp.operation_info)

    async def describe_batch_operation(self, namespace: str, job_id: str) -> Any:  # noqa: ANN401
        """Return the full DescribeBatchOperationResponse for one job.

        Args:
            namespace: Target namespace.
            job_id: Batch job id.

        Returns:
            The DescribeBatchOperationResponse proto.
        """
        client = await self._pool.get(namespace)
        return await client.workflow_service.describe_batch_operation(
            DescribeBatchOperationRequest(namespace=namespace, job_id=job_id)
        )

    async def stop_batch_operation(
        self, namespace: str, job_id: str, reason: str, identity: str = "temporal-mcp"
    ) -> None:
        """Stop a running batch operation. (Mutating).

        Args:
            namespace: Target namespace.
            job_id: Batch job id.
            reason: Reason for stopping.
            identity: Caller identity recorded on the batch job.
        """
        client = await self._pool.get(namespace)
        await client.workflow_service.stop_batch_operation(
            StopBatchOperationRequest(namespace=namespace, job_id=job_id, reason=reason, identity=identity)
        )
