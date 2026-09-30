"""Deployment configuration and audit wiring."""

import asyncio

import pytest
from pydantic import ValidationError

from temporal_mcp.audit import AuditMiddleware
from temporal_mcp.config import McpServerConfig
from temporal_mcp.main import build


def test_runtime_environment(monkeypatch):
    monkeypatch.setenv("MCP_PATH", "/temporal/mcp")
    monkeypatch.setenv("MCP_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("MCP_AUDIT_TRUSTED_USER_HEADER", "X-Authenticated-User")
    config = McpServerConfig(_env_file=None)
    assert config.path == "/temporal/mcp"
    assert config.log_level == "WARNING"
    middleware = asyncio.run(build(config)).middleware
    assert isinstance(middleware[0], AuditMiddleware)
    assert middleware[0]._trusted_user_header == "X-Authenticated-User"


def test_audit_can_be_disabled(monkeypatch):
    monkeypatch.setenv("MCP_AUDIT_ENABLED", "false")
    server = asyncio.run(build(McpServerConfig(_env_file=None)))
    assert not any(isinstance(item, AuditMiddleware) for item in server.middleware)


@pytest.mark.parametrize("settings", [{"port": 0}, {"port": 65536}, {"path": "mcp"}, {"log_level": "invalid"}])
def test_invalid_runtime_configuration_fails(settings):
    with pytest.raises(ValidationError):
        McpServerConfig(_env_file=None, **settings)
