"""Tests for the activity service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.activity_service import TemporalActivityService


class _FakeClient:
    """Mimics temporalio's Client.list_activities: bounds results server-side via `limit`."""

    def __init__(self):
        self.list_query = None
        self.list_limit = None

    def list_activities(self, query, *, limit=None):
        self.list_query = query
        self.list_limit = limit

        async def gen():
            count = 5 if limit is None else min(5, limit)
            for i in range(count):
                yield MagicMock(activity_id=f"a{i}")

        return gen()


def _svc(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalActivityService(pool)


def test_list_activities_limits_and_passes_query():
    client = _FakeClient()
    svc = _svc(client)
    out = asyncio.run(svc.list_activities("ns", query='ActivityType="X"', limit=2))
    assert len(out) == 2
    assert client.list_query == 'ActivityType="X"'


def test_list_activities_passes_limit_to_sdk_for_server_side_paging():
    client = _FakeClient()
    svc = _svc(client)
    out = asyncio.run(svc.list_activities("ns", limit=3))
    assert len(out) == 3
    assert client.list_limit == 3


def test_list_activities_default_query_is_empty_string():
    client = _FakeClient()
    svc = _svc(client)
    asyncio.run(svc.list_activities("ns"))
    assert client.list_query == ""


def test_describe_activity_uses_handle():
    handle = MagicMock()
    handle.describe = AsyncMock(return_value="DESC")
    client = MagicMock()
    client.get_activity_handle = MagicMock(return_value=handle)
    svc = _svc(client)
    out = asyncio.run(svc.describe_activity("ns", "aid", run_id="rid"))
    assert out == "DESC"
    client.get_activity_handle.assert_called_once_with("aid", run_id="rid")
