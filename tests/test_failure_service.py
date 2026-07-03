import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services import failure_service
from temporal_mcp.services.failure_service import TemporalFailureService, _failed_query


def test_failure_service_does_not_import_mapper():
    assert not hasattr(failure_service, "failure_mapper")


def _fail(message, *, info=None, info_val=None, cause=None):
    class _F:
        def __init__(self):
            self.message = message
            self.source = ""
            self.stack_trace = ""
            self.cause = cause

        def WhichOneof(self, oneof):  # noqa: N802
            return info

        def HasField(self, name):  # noqa: N802
            return name == "cause" and cause is not None

    f = _F()
    if info:
        setattr(f, info, info_val)
    return f


class _Event:
    def __init__(self, attr, value):
        self._attr = attr
        setattr(self, attr, value)

    def HasField(self, name):  # noqa: N802
        return name == self._attr


def _failed_history():
    failure = _fail("root", info="application_failure_info", info_val=SimpleNamespace(type="E"))
    return SimpleNamespace(
        events=[_Event("workflow_execution_failed_event_attributes", SimpleNamespace(failure=failure))]
    )


def test_failed_query_with_and_without_since():
    assert _failed_query(None) == 'ExecutionStatus="Failed"'
    assert _failed_query("2026-01-01T00:00:00Z") == 'ExecutionStatus="Failed" AND StartTime > "2026-01-01T00:00:00Z"'


def test_fetch_workflow_failure_data():
    handle = MagicMock()
    handle.describe = AsyncMock(
        return_value=SimpleNamespace(
            status=SimpleNamespace(name="FAILED"), workflow_type="W", close_time=None, run_id="r"
        )
    )
    handle.fetch_history = AsyncMock(return_value=_failed_history())
    client = MagicMock()
    client.get_workflow_handle.return_value = handle
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)

    svc = TemporalFailureService(pool)
    out = asyncio.run(svc.fetch_workflow_failure_data("ns", "wf"))
    assert out.namespace == "ns"
    assert out.workflow_id == "wf"
    assert out.description.status.name == "FAILED"
    assert out.history.events[0].workflow_execution_failed_event_attributes.failure.message == "root"


def test_summarize_uses_group_by_and_sample():
    count = SimpleNamespace(count=2, groups=[SimpleNamespace(count=2, group_values=["W"])])
    handle = MagicMock()
    handle.fetch_history = AsyncMock(return_value=_failed_history())
    client = MagicMock()
    client.count_workflows = AsyncMock(return_value=count)
    client.get_workflow_handle.return_value = handle

    def _list(query, *, limit):
        async def gen():
            for i in range(2):
                yield SimpleNamespace(id=f"wf{i}", run_id="r")

        return gen()

    client.list_workflows = _list
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)

    svc = TemporalFailureService(pool)
    data = asyncio.run(svc.fetch_namespace_failure_data("ns", sample_size=5))
    assert data.count.count == 2
    assert data.count.groups[0].group_values == ["W"]
    assert len(data.histories) == 2
    assert client.count_workflows.call_args[0][0].endswith("GROUP BY WorkflowType")


def test_summarize_falls_back_when_group_by_rejected():
    plain = SimpleNamespace(count=4, groups=[])
    client = MagicMock()
    client.count_workflows = AsyncMock(side_effect=[RuntimeError("group by unsupported"), plain])

    def _list(query, *, limit):
        async def gen():
            if False:
                yield None

        return gen()

    client.list_workflows = _list
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)

    svc = TemporalFailureService(pool)
    data = asyncio.run(svc.fetch_namespace_failure_data("ns"))
    assert data.count.count == 4
    assert data.count.groups == []
    assert data.histories == []
    assert client.count_workflows.call_count == 2


def test_fetch_failure_histories_samples_failed_workflows():
    handle = MagicMock()
    handle.fetch_history = AsyncMock(return_value=_failed_history())
    client = MagicMock()
    client.get_workflow_handle.return_value = handle

    def _list(query, *, limit):
        async def gen():
            for i in range(3):
                yield SimpleNamespace(id=f"wf{i}", run_id="r")

        return gen()

    client.list_workflows = _list
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)

    svc = TemporalFailureService(pool)
    histories = asyncio.run(svc.fetch_failure_histories("ns", sample_size=5))
    assert len(histories) == 3
