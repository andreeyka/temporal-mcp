"""Activity execution read operations within a namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalActivityService:
    """List and describe standalone activity executions."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_activities(self, namespace: str, query: str | None = None, limit: int = 50) -> list[Any]:
        """List up to ``limit`` activity executions matching a visibility query.

        Args:
            namespace: Target namespace.
            query: Optional visibility query.
            limit: Maximum number of activities.

        Returns:
            A list of ActivityExecution objects (length ≤ limit).
        """
        client = await self._pool.get(namespace)
        return [activity async for activity in client.list_activities(query or "", limit=limit)]

    async def describe_activity(self, namespace: str, activity_id: str, run_id: str | None = None) -> Any:  # noqa: ANN401
        """Return the detailed description for one activity execution."""
        client = await self._pool.get(namespace)
        return await client.get_activity_handle(activity_id, run_id=run_id).describe()
