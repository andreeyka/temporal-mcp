"""Failure-analysis operations over the client pool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


@dataclass(frozen=True)
class _WorkflowFailureData:
    """Raw workflow failure inputs fetched from Temporal."""

    namespace: str
    workflow_id: str
    run_id: str | None
    description: object
    history: object


@dataclass(frozen=True)
class _NamespaceFailureData:
    """Raw namespace failure inputs fetched from Temporal."""

    namespace: str
    since: str | None
    count: object
    histories: list[object]
    sample_size: int


def _failed_query(since: str | None) -> str:
    """Build a visibility query selecting failed executions, optionally since a time."""
    base = 'ExecutionStatus="Failed"'
    return f'{base} AND StartTime > "{since}"' if since else base


class TemporalFailureService:
    """Root-cause analysis and namespace failure aggregation."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the shared client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def fetch_workflow_failure_data(
        self, namespace: str, workflow_id: str, run_id: str | None = None
    ) -> _WorkflowFailureData:
        """Fetch raw inputs needed to analyze a workflow failure.

        Args:
            namespace: Target namespace.
            workflow_id: Workflow id to fetch.
            run_id: Optional run id.

        Returns:
            Raw describe and history data for mapper conversion.
        """
        client = await self._pool.get(namespace)
        handle = client.get_workflow_handle(workflow_id, run_id=run_id)
        desc = await handle.describe()
        history = await handle.fetch_history()
        return _WorkflowFailureData(namespace, workflow_id, run_id, desc, history)

    async def fetch_namespace_failure_data(
        self, namespace: str, since: str | None = None, sample_size: int = 100
    ) -> _NamespaceFailureData:
        """Fetch raw inputs needed to summarize namespace failures.

        Args:
            namespace: Target namespace.
            since: Optional ISO-8601 lower bound on StartTime.
            sample_size: Max failed workflows to sample for error-type breakdown.

        Returns:
            Raw count and history sample data for mapper conversion.
        """
        client = await self._pool.get(namespace)
        query = _failed_query(since)
        count = await self._count_failed(client, query)
        histories = await self._sample_histories(client, query, sample_size)
        return _NamespaceFailureData(namespace, since, count, histories, sample_size)

    async def fetch_failure_histories(
        self, namespace: str, since: str | None = None, sample_size: int = 100
    ) -> list[object]:
        """Fetch raw histories for a bounded sample of failed workflows.

        Args:
            namespace: Target namespace.
            since: Optional ISO-8601 lower bound on StartTime.
            sample_size: Max failed workflows to sample.

        Returns:
            Raw workflow histories.
        """
        client = await self._pool.get(namespace)
        return await self._sample_histories(client, _failed_query(since), sample_size)

    async def _count_failed(self, client: Any, query: str) -> Any:  # noqa: ANN401
        """Count failed executions grouped by workflow type, falling back to a plain count."""
        try:
            return await client.count_workflows(f"{query} GROUP BY WorkflowType")
        except Exception:
            # Not every namespace's visibility store supports count-aggregation
            # (GROUP BY) queries — e.g. standard visibility without an advanced
            # backend. Fall back to a plain count so the summary still reports
            # an exact total, just without the by-workflow-type breakdown.
            return await client.count_workflows(query)

    async def _sample_histories(self, client: Any, query: str, sample_size: int) -> list[object]:  # noqa: ANN401
        """Fetch histories for a bounded sample of failed workflows."""
        histories: list[object] = []
        async for execution in client.list_workflows(query, limit=sample_size):
            history = await client.get_workflow_handle(execution.id, run_id=execution.run_id).fetch_history()
            histories.append(history)
        return histories
