import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.workflow_service import TemporalWorkflowService


class _FakeClient:
    def __init__(self):
        self.calls = []

    def list_workflows(self, query, *, limit):
        self.calls.append(("list", query, limit))

        async def gen():
            for i in range(3):
                yield MagicMock(name=f"ex{i}")

        return gen()


def test_list_workflows_composes_query():
    client = _FakeClient()
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    svc = TemporalWorkflowService(pool)
    out = asyncio.run(svc.list_workflows("ns", query='WorkflowType="Foo"', status="FAILED", limit=2))
    assert len(out) == 2
    assert client.calls[0][1] == 'WorkflowType="Foo" AND ExecutionStatus="Failed"'
    assert client.calls[0][2] == 2
