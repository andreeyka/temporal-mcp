"""Tests for schedule create/update/trigger/backfill service methods."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from temporalio.client import ScheduleOverlapPolicy

from temporal_mcp.errors import InvalidScheduleSpecError
from temporal_mcp.services.schedule_service import TemporalScheduleService


def _svc(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalScheduleService(pool)


def test_create_schedule_builds_cron_spec():
    handle = MagicMock(id="sid")
    client = MagicMock()
    client.create_schedule = AsyncMock(return_value=handle)
    svc = _svc(client)
    asyncio.run(svc.create_schedule("ns", "sid", "MyType", "tq", "wf", cron="0 * * * *", args=[1]))
    sid, schedule = client.create_schedule.call_args.args
    assert sid == "sid"
    assert schedule.spec.cron_expressions == ["0 * * * *"]
    assert schedule.action.workflow == "MyType"
    assert schedule.action.id == "wf"
    assert schedule.action.task_queue == "tq"


def test_create_schedule_builds_interval_spec():
    handle = MagicMock(id="sid")
    client = MagicMock()
    client.create_schedule = AsyncMock(return_value=handle)
    svc = _svc(client)
    asyncio.run(svc.create_schedule("ns", "sid", "MyType", "tq", "wf", interval_seconds=3600))
    _, schedule = client.create_schedule.call_args.args
    assert schedule.spec.intervals[0].every.total_seconds() == 3600


def test_create_schedule_requires_spec():
    client = MagicMock()
    client.create_schedule = AsyncMock()
    svc = _svc(client)
    with pytest.raises(InvalidScheduleSpecError):
        asyncio.run(svc.create_schedule("ns", "sid", "MyType", "tq", "wf"))


def test_create_schedule_requires_spec_rejects_zero_interval():
    """interval_seconds=0 is falsy but explicitly provided; it must not silently build an empty spec."""
    client = MagicMock()
    client.create_schedule = AsyncMock()
    svc = _svc(client)
    with pytest.raises(InvalidScheduleSpecError):
        asyncio.run(svc.create_schedule("ns", "sid", "MyType", "tq", "wf", interval_seconds=0))


def test_create_schedule_rejects_both_cron_and_interval():
    client = MagicMock()
    client.create_schedule = AsyncMock()
    svc = _svc(client)
    with pytest.raises(InvalidScheduleSpecError):
        asyncio.run(svc.create_schedule("ns", "sid", "MyType", "tq", "wf", cron="0 * * * *", interval_seconds=3600))


def test_update_schedule_replaces_spec():
    handle = MagicMock()
    handle.update = AsyncMock()
    client = MagicMock()
    client.get_schedule_handle = MagicMock(return_value=handle)
    svc = _svc(client)
    asyncio.run(svc.update_schedule("ns", "sid", cron="* * * * *"))
    updater = handle.update.call_args.args[0]
    inp = MagicMock()
    inp.description.schedule = MagicMock()
    result = updater(inp)
    assert result.schedule.spec.cron_expressions == ["* * * * *"]


def test_trigger_schedule_maps_overlap():
    handle = MagicMock()
    handle.trigger = AsyncMock()
    client = MagicMock()
    client.get_schedule_handle = MagicMock(return_value=handle)
    svc = _svc(client)
    asyncio.run(svc.trigger_schedule("ns", "sid", overlap="SKIP"))
    assert handle.trigger.call_args.kwargs["overlap"] == ScheduleOverlapPolicy.SKIP


def test_backfill_schedule_builds_range():
    handle = MagicMock()
    handle.backfill = AsyncMock()
    client = MagicMock()
    client.get_schedule_handle = MagicMock(return_value=handle)
    svc = _svc(client)
    asyncio.run(
        svc.backfill_schedule("ns", "sid", "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", overlap="BUFFER_ONE")
    )
    bf = handle.backfill.call_args.args[0]
    assert bf.start_at == datetime.fromisoformat("2026-01-01T00:00:00Z")
    assert bf.end_at == datetime.fromisoformat("2026-01-02T00:00:00Z")
    assert bf.overlap == ScheduleOverlapPolicy.BUFFER_ONE
