"""Tests for the entry-point server build."""

import asyncio
import logging

import pytest

from temporal_mcp.config import IdpConfig, McpServerConfig, TemporalConfig
from temporal_mcp.enums import AuthMode, IncomingAuthMode
from temporal_mcp.errors import IncomingAuthConfigError, MissingAuthVerifierError
from temporal_mcp.main import _build_auth, build


def test_build_auth_none_mode_returns_none_in_service():
    cfg = McpServerConfig(auth_mode=IncomingAuthMode.NONE, temporal=TemporalConfig(auth_mode=AuthMode.SERVICE))
    assert _build_auth(cfg) is None


def test_build_auth_none_mode_raises_for_passthrough():
    cfg = McpServerConfig(auth_mode=IncomingAuthMode.NONE, temporal=TemporalConfig(auth_mode=AuthMode.PASSTHROUGH))
    with pytest.raises(MissingAuthVerifierError):
        _build_auth(cfg)


def test_build_auth_keycloak_requires_issuer():
    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url="https://mcp.example.com",
        idp=IdpConfig(issuer=None),
    )
    with pytest.raises(IncomingAuthConfigError):
        _build_auth(cfg)


def test_build_auth_keycloak_requires_base_url():
    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url=None,
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo"),
    )
    with pytest.raises(IncomingAuthConfigError):
        _build_auth(cfg)


def test_build_auth_keycloak_requires_audience():
    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url="https://mcp.example.com",
        auth_audience=None,
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo", audience=None),
    )
    with pytest.raises(IncomingAuthConfigError):
        _build_auth(cfg)


def test_build_auth_keycloak_builds_provider():
    from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider

    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url="https://mcp.example.com",
        auth_audience="temporal-api",
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo"),
    )
    assert isinstance(_build_auth(cfg), KeycloakAuthProvider)


def test_build_auth_keycloak_allows_no_audience_when_not_required():
    from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider

    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url="https://mcp.example.com",
        auth_audience=None,
        auth_require_audience=False,
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo", audience=None),
    )
    # Deliberate opt-out: builds a provider with aud validation disabled instead of raising.
    assert isinstance(_build_auth(cfg), KeycloakAuthProvider)


def test_build_adds_claim_expression_middleware():
    from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider

    from temporal_mcp.middleware import ClaimExpressionMiddleware

    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url="https://mcp.example.com",
        auth_audience="temporal-api",
        auth_claim_expr='"Example-Admins" in groups',
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo"),
    )
    app = asyncio.run(build(cfg))
    assert isinstance(app.auth, KeycloakAuthProvider)
    assert any(isinstance(mw, ClaimExpressionMiddleware) for mw in app.middleware)


def test_build_logs_incoming_auth_policy(caplog):
    caplog.set_level(logging.INFO)
    cfg = McpServerConfig(
        auth_mode=IncomingAuthMode.KEYCLOAK,
        auth_base_url="https://mcp.example.com",
        auth_audience="temporal-api",
        auth_claim_expr='"Example-Admins" in groups',
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo"),
    )
    asyncio.run(build(cfg))
    assert "Incoming MCP auth configured" in caplog.text
    assert "Incoming claim expression policy loaded" in caplog.text
    assert '"Example-Admins" in groups' in caplog.text


def test_build_returns_server():
    app = asyncio.run(build(McpServerConfig()))
    assert app is not None
    assert app.name


def test_build_registers_failure_tools():
    app = asyncio.run(build(McpServerConfig()))
    for name in ("analyze_workflow_failure", "summarize_namespace_failures", "top_failure_types"):
        assert asyncio.run(app.get_tool(name)) is not None


def test_tool_search_hides_catalog():
    app = asyncio.run(build(McpServerConfig()))
    listed = {t.name for t in asyncio.run(app.list_tools())}
    assert {"search_tools", "call_tool"} <= listed
    # the raw catalog is hidden behind search
    assert "terminate_workflow" not in listed
    assert "list_workflows" not in listed


def test_tool_search_disabled_exposes_catalog():
    cfg = McpServerConfig(tool_search=False, temporal=TemporalConfig(auth_mode=AuthMode.SERVICE))
    app = asyncio.run(build(cfg))
    listed = {t.name for t in asyncio.run(app.list_tools())}
    assert "search_tools" not in listed
    assert "call_tool" not in listed
    # the raw catalog is exposed directly
    assert "list_workflows" in listed


def test_run_forwards_stateless_http(monkeypatch):
    import asyncio

    from temporal_mcp import main

    captured = {}

    class _App:
        async def run_async(self, **kwargs):
            captured.update(kwargs)

    async def _fake_build(cfg):
        return _App()

    monkeypatch.setattr(main, "build", _fake_build)
    monkeypatch.setattr(main.mcp_config, "stateless_http", True)
    asyncio.run(main.run())
    assert captured.get("stateless_http") is True


def test_build_registers_rpc_error_middleware():
    from temporal_mcp.middleware import TemporalRpcErrorMiddleware

    cfg = McpServerConfig(auth_mode=IncomingAuthMode.NONE, temporal=TemporalConfig(auth_mode=AuthMode.SERVICE))
    app = asyncio.run(build(cfg))
    assert any(isinstance(mw, TemporalRpcErrorMiddleware) for mw in app.middleware)
