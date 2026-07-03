"""Task queue and search-attribute read operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from temporalio.api.operatorservice.v1 import ListSearchAttributesRequest
from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalTaskQueueService:
    """Describe task queues and list search attributes."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def describe_task_queue(self, namespace: str, task_queue: str) -> Any:  # noqa: ANN401
        """Return pollers/reachability for a task queue."""
        client = await self._pool.get(namespace)
        return await client.workflow_service.describe_task_queue(
            DescribeTaskQueueRequest(namespace=namespace, task_queue=TaskQueue(name=task_queue))
        )

    async def list_search_attributes(self, namespace: str) -> Any:  # noqa: ANN401
        """Return custom and system search attributes for a namespace."""
        client = await self._pool.get(namespace)
        return await client.operator_service.list_search_attributes(ListSearchAttributesRequest(namespace=namespace))
