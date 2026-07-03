"""Workflow read and mutation operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from temporalio.api.common.v1 import WorkflowExecution
from temporalio.api.workflowservice.v1 import (
    CountWorkflowExecutionsRequest,
    PauseWorkflowExecutionRequest,
    ResetWorkflowExecutionRequest,
    UnpauseWorkflowExecutionRequest,
)

from temporal_mcp.utils.query import status_to_query


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalWorkflowService:
    """Operations on workflow executions within a namespace."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_workflows(
        self, namespace: str, query: str | None = None, status: str | None = None, limit: int = 50
    ) -> list[Any]:
        """List executions, ANDing an optional status filter into the query.

        Args:
            namespace: Target namespace.
            query: Optional visibility query.
            status: Optional status convenience filter (FAILED, RUNNING, ...).
            limit: Maximum number of executions.

        Returns:
            A list of WorkflowExecution objects (length ≤ limit).

        Raises:
            UnknownWorkflowStatusError: If status is not a valid status.
        """
        client = await self._pool.get(namespace)
        parts = [p for p in (query, status_to_query(status)) if p]
        full = " AND ".join(parts)
        results: list[Any] = []
        async for ex in client.list_workflows(full, limit=limit):
            results.append(ex)
            if len(results) >= limit:
                break
        return results

    async def describe_workflow(self, namespace: str, workflow_id: str, run_id: str | None = None) -> Any:  # noqa: ANN401
        """Return the execution description for one workflow."""
        client = await self._pool.get(namespace)
        return await client.get_workflow_handle(workflow_id, run_id=run_id).describe()

    async def get_workflow_history(self, namespace: str, workflow_id: str, run_id: str | None = None) -> Any:  # noqa: ANN401
        """Return the event history for one workflow."""
        client = await self._pool.get(namespace)
        return await client.get_workflow_handle(workflow_id, run_id=run_id).fetch_history()

    async def count_workflows(self, namespace: str, query: str | None = None) -> Any:  # noqa: ANN401
        """Count executions matching a visibility query."""
        client = await self._pool.get(namespace)
        return await client.workflow_service.count_workflow_executions(
            CountWorkflowExecutionsRequest(namespace=namespace, query=query or "")
        )

    async def start_workflow(
        self, namespace: str, workflow_type: str, task_queue: str, workflow_id: str, args: list[Any] | None = None
    ) -> Any:  # noqa: ANN401
        """Start a new workflow execution (mutating)."""
        client = await self._pool.get(namespace)
        return await client.start_workflow(workflow_type, *(args or []), id=workflow_id, task_queue=task_queue)

    async def signal_workflow(
        self, namespace: str, workflow_id: str, signal: str, args: list[Any] | None = None, run_id: str | None = None
    ) -> None:
        """Send a signal to a running workflow (mutating)."""
        client = await self._pool.get(namespace)
        await client.get_workflow_handle(workflow_id, run_id=run_id).signal(signal, *(args or []))

    async def query_workflow(
        self,
        namespace: str,
        workflow_id: str,
        query_name: str,
        args: list[Any] | None = None,
        run_id: str | None = None,
    ) -> Any:  # noqa: ANN401
        """Query workflow state via a registered query handler."""
        client = await self._pool.get(namespace)
        return await client.get_workflow_handle(workflow_id, run_id=run_id).query(query_name, *(args or []))

    async def cancel_workflow(self, namespace: str, workflow_id: str, run_id: str | None = None) -> None:
        """Request graceful cancellation (mutating)."""
        client = await self._pool.get(namespace)
        await client.get_workflow_handle(workflow_id, run_id=run_id).cancel()

    async def terminate_workflow(
        self, namespace: str, workflow_id: str, reason: str = "", run_id: str | None = None
    ) -> None:
        """Force-terminate a workflow immediately (mutating, destructive)."""
        client = await self._pool.get(namespace)
        await client.get_workflow_handle(workflow_id, run_id=run_id).terminate(reason)

    async def pause_workflow(
        self, namespace: str, workflow_id: str, reason: str = "", run_id: str | None = None
    ) -> None:
        """Pause a running workflow, stopping new workflow-task scheduling (mutating)."""
        client = await self._pool.get(namespace)
        await client.workflow_service.pause_workflow_execution(
            PauseWorkflowExecutionRequest(
                namespace=namespace,
                workflow_id=workflow_id,
                run_id=run_id or "",
                reason=reason,
                request_id=str(uuid.uuid4()),
            )
        )

    async def unpause_workflow(
        self, namespace: str, workflow_id: str, reason: str = "", run_id: str | None = None
    ) -> None:
        """Resume a paused workflow (mutating)."""
        client = await self._pool.get(namespace)
        await client.workflow_service.unpause_workflow_execution(
            UnpauseWorkflowExecutionRequest(
                namespace=namespace,
                workflow_id=workflow_id,
                run_id=run_id or "",
                reason=reason,
                request_id=str(uuid.uuid4()),
            )
        )

    async def signal_with_start_workflow(
        self,
        namespace: str,
        workflow_type: str,
        task_queue: str,
        workflow_id: str,
        signal: str,
        signal_args: list[Any] | None = None,
        args: list[Any] | None = None,
    ) -> Any:  # noqa: ANN401
        """Start a workflow and deliver a signal atomically, or signal if already running (mutating)."""
        client = await self._pool.get(namespace)
        return await client.start_workflow(
            workflow_type,
            *(args or []),
            id=workflow_id,
            task_queue=task_queue,
            start_signal=signal,
            start_signal_args=signal_args or [],
        )

    async def update_workflow(
        self, namespace: str, workflow_id: str, update: str, args: list[Any] | None = None, run_id: str | None = None
    ) -> Any:  # noqa: ANN401
        """Send an update to a running workflow and wait for its result (mutating)."""
        client = await self._pool.get(namespace)
        handle = client.get_workflow_handle(workflow_id, run_id=run_id)
        return await handle.execute_update(update, args=args or [])

    async def reset_workflow(
        self, namespace: str, workflow_id: str, event_id: int, reason: str = "", run_id: str | None = None
    ) -> Any:  # noqa: ANN401
        """Reset a workflow to a prior history event, abandoning the run and creating a new one (destructive)."""
        client = await self._pool.get(namespace)
        return await client.workflow_service.reset_workflow_execution(
            ResetWorkflowExecutionRequest(
                namespace=namespace,
                workflow_execution=WorkflowExecution(workflow_id=workflow_id, run_id=run_id or ""),
                reason=reason,
                workflow_task_finish_event_id=event_id,
                request_id=str(uuid.uuid4()),
            )
        )
