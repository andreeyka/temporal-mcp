"""Schedule operations within a namespace."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleBackfill,
    ScheduleIntervalSpec,
    ScheduleOverlapPolicy,
    ScheduleSpec,
    ScheduleUpdate,
    ScheduleUpdateInput,
)

from temporal_mcp.errors import InvalidScheduleSpecError


if TYPE_CHECKING:
    from temporal_mcp.services.client_service import TemporalClientPool


class TemporalScheduleService:
    """List/describe/pause/unpause/delete schedules."""

    def __init__(self, pool: TemporalClientPool) -> None:
        """Initialize with the client pool.

        Args:
            pool: The shared Temporal client pool.
        """
        self._pool = pool

    async def list_schedules(self, namespace: str, limit: int = 50) -> list[Any]:
        """Return up to ``limit`` schedules in the namespace."""
        client = await self._pool.get(namespace)
        out: list[Any] = []
        async for s in await client.list_schedules():
            out.append(s)
            if len(out) >= limit:
                break
        return out

    async def describe_schedule(self, namespace: str, schedule_id: str) -> Any:  # noqa: ANN401
        """Return a schedule description."""
        client = await self._pool.get(namespace)
        return await client.get_schedule_handle(schedule_id).describe()

    async def pause_schedule(self, namespace: str, schedule_id: str, note: str = "") -> None:
        """Pause a schedule (mutating)."""
        client = await self._pool.get(namespace)
        await client.get_schedule_handle(schedule_id).pause(note=note)

    async def unpause_schedule(self, namespace: str, schedule_id: str, note: str = "") -> None:
        """Resume a paused schedule (mutating)."""
        client = await self._pool.get(namespace)
        await client.get_schedule_handle(schedule_id).unpause(note=note)

    async def delete_schedule(self, namespace: str, schedule_id: str) -> None:
        """Delete a schedule (mutating, destructive)."""
        client = await self._pool.get(namespace)
        await client.get_schedule_handle(schedule_id).delete()

    async def create_schedule(
        self,
        namespace: str,
        schedule_id: str,
        workflow_type: str,
        task_queue: str,
        workflow_id: str,
        cron: str | None = None,
        interval_seconds: int | None = None,
        args: list[Any] | None = None,
    ) -> Any:  # noqa: ANN401
        """Create a cron- or interval-based schedule that starts a workflow (mutating)."""
        client = await self._pool.get(namespace)
        action = ScheduleActionStartWorkflow(workflow_type, args=args or [], id=workflow_id, task_queue=task_queue)
        schedule = Schedule(action=action, spec=self._build_spec(cron, interval_seconds))
        return await client.create_schedule(schedule_id, schedule)

    async def update_schedule(
        self, namespace: str, schedule_id: str, cron: str | None = None, interval_seconds: int | None = None
    ) -> None:
        """Replace a schedule's spec with a new cron/interval spec (mutating)."""
        client = await self._pool.get(namespace)
        spec = self._build_spec(cron, interval_seconds)

        def _updater(inp: ScheduleUpdateInput) -> ScheduleUpdate:
            schedule = inp.description.schedule
            schedule.spec = spec
            return ScheduleUpdate(schedule=schedule)

        await client.get_schedule_handle(schedule_id).update(_updater)

    async def trigger_schedule(self, namespace: str, schedule_id: str, overlap: str | None = None) -> None:
        """Trigger a schedule action immediately (mutating)."""
        client = await self._pool.get(namespace)
        await client.get_schedule_handle(schedule_id).trigger(overlap=self._overlap(overlap))

    async def backfill_schedule(
        self, namespace: str, schedule_id: str, start_at: str, end_at: str, overlap: str | None = None
    ) -> None:
        """Backfill a schedule over an ISO-8601 time range (mutating)."""
        client = await self._pool.get(namespace)
        await client.get_schedule_handle(schedule_id).backfill(
            ScheduleBackfill(
                start_at=datetime.fromisoformat(start_at),
                end_at=datetime.fromisoformat(end_at),
                overlap=self._overlap(overlap),
            )
        )

    @staticmethod
    def _build_spec(cron: str | None, interval_seconds: int | None) -> ScheduleSpec:
        """Build a ScheduleSpec from a cron expression or an interval in seconds.

        Exactly one of `cron` or `interval_seconds` must be provided.

        Raises:
            InvalidScheduleSpecError: If neither, or both, cron and interval are provided.
        """
        if not cron and not interval_seconds:
            raise InvalidScheduleSpecError
        if cron and interval_seconds:
            raise InvalidScheduleSpecError
        intervals = [ScheduleIntervalSpec(every=timedelta(seconds=interval_seconds))] if interval_seconds else []
        return ScheduleSpec(cron_expressions=[cron] if cron else [], intervals=intervals)

    @staticmethod
    def _overlap(overlap: str | None) -> ScheduleOverlapPolicy | None:
        """Map an overlap-policy name to the enum, or None."""
        return ScheduleOverlapPolicy[overlap] if overlap else None
