"""Audit identity, outcomes, and payload privacy."""

import asyncio
import json
import logging

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AccessToken
from fastmcp.server.middleware import MiddlewareContext
from fastmcp.server.transforms.search import BM25SearchTransform
from fastmcp.tools import ToolResult
from mcp.types import CallToolRequestParams
from starlette.requests import Request

from temporal_mcp import audit


@pytest.mark.parametrize(
    ("claims", "expected"),
    [({"preferred_username": "alice", "sub": "user-1"}, "alice"), ({"sub": "user-1"}, "user-1"), ({}, "client-1")],
)
def test_verified_identity_precedes_header(monkeypatch, claims, expected):
    token = AccessToken(token="secret-token", client_id="client-1", scopes=[], claims=claims)
    monkeypatch.setattr(audit, "get_access_token", lambda: token)
    assert audit.current_user("X-User") == expected


def test_header_identity_requires_explicit_configuration(monkeypatch):
    request = Request({"type": "http", "headers": [(b"x-user", b"alice")]})
    monkeypatch.setattr(audit, "get_access_token", lambda: None)
    monkeypatch.setattr(audit, "get_http_request", lambda: request)
    assert audit.current_user() == "anonymous"
    assert audit.current_user("X-User") == "alice"
    assert audit.current_user("X-Missing") == "anonymous"


def _example_server(outcome, search):
    app = FastMCP(middleware=[audit.AuditMiddleware()], transforms=[BM25SearchTransform()] if search else [])

    @app.tool
    async def example(payload: str) -> ToolResult:
        if outcome == "raised_error":
            raise ToolError(payload)
        return ToolResult(content=payload, is_error=outcome == "returned_error")

    return app


async def _call_example(app, search):
    async with Client(app) as client:
        arguments = {"payload": "secret-payload"}
        if search:
            return await client.call_tool(
                "call_tool", {"name": "example", "arguments": arguments}, raise_on_error=False
            )
        return await client.call_tool("example", arguments, raise_on_error=False)


@pytest.mark.parametrize("outcome", ["ok", "returned_error", "raised_error"])
@pytest.mark.parametrize("search", [False, True])
def test_audit_records_outcome_without_payloads(caplog, outcome, search):
    caplog.set_level(logging.INFO, logger="temporal_mcp.audit")
    result = asyncio.run(_call_example(_example_server(outcome, search), search))
    assert result.is_error == (outcome != "ok")
    records = [json.loads(record.message) for record in caplog.records if record.name == "temporal_mcp.audit"]
    assert [record["tool"] for record in records] == (["example", "call_tool"] if search else ["example"])
    if search:
        assert records[-1]["target_tool"] == "example"
    record = next(record for record in records if record["tool"] == "example")
    assert record["user"] == "anonymous"
    assert record["outcome"].startswith("error") == (outcome != "ok")
    assert record["duration_ms"] >= 0
    assert "secret-payload" not in json.dumps(records)


def test_cancelled_call_is_audited_and_propagates(caplog):
    caplog.set_level(logging.INFO, logger="temporal_mcp.audit")
    context = MiddlewareContext(message=CallToolRequestParams(name="example"))

    async def cancelled(_context):
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(audit.AuditMiddleware().on_call_tool(context, cancelled))
    records = [json.loads(record.message) for record in caplog.records if record.name == "temporal_mcp.audit"]
    assert len(records) == 1
    assert records[0]["outcome"] == "cancelled"
