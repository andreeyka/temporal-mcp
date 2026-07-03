import importlib

from temporal_mcp.enums import AuthMode, TransportType


def test_defaults(monkeypatch):
    for var in list(__import__("os").environ):
        if var.startswith(("MCP_", "TEMPORAL_")):
            monkeypatch.delenv(var, raising=False)
    import temporal_mcp.config as cfg

    importlib.reload(cfg)
    c = cfg.McpServerConfig(
        _env_file=None,
        temporal=cfg.TemporalConfig(_env_file=None),
        idp=cfg.IdpConfig(_env_file=None),
    )
    assert c.transport == TransportType.HTTP
    assert c.temporal.host == "localhost:7233"
    assert c.temporal.auth_mode == AuthMode.SERVICE
    assert c.temporal.pool_max == 64


def test_temporal_env_override(monkeypatch):
    monkeypatch.setenv("TEMPORAL_HOST", "frontend:7233")
    monkeypatch.setenv("TEMPORAL_AUTH_MODE", "passthrough")
    import temporal_mcp.config as cfg

    importlib.reload(cfg)
    c = cfg.McpServerConfig()
    assert c.temporal.host == "frontend:7233"
    assert c.temporal.auth_mode == AuthMode.PASSTHROUGH


def test_read_only_defaults_false():
    from temporal_mcp.config import McpServerConfig

    assert McpServerConfig().read_only is False


def test_tool_search_defaults_true():
    from temporal_mcp.config import McpServerConfig

    assert McpServerConfig().tool_search is True


def test_tool_search_env_override(monkeypatch):
    monkeypatch.setenv("MCP_TOOL_SEARCH", "false")
    from temporal_mcp.config import McpServerConfig

    assert McpServerConfig().tool_search is False


def test_auth_require_audience_defaults_true():
    from temporal_mcp.config import McpServerConfig

    # secure by default: audience validation is on unless explicitly opted out
    assert McpServerConfig().auth_require_audience is True


def test_auth_require_audience_env_override(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_REQUIRE_AUDIENCE", "false")
    from temporal_mcp.config import McpServerConfig

    assert McpServerConfig().auth_require_audience is False


def test_idp_derives_endpoints_from_issuer(monkeypatch):
    for var in list(__import__("os").environ):
        if var.startswith("IDP_"):
            monkeypatch.delenv(var, raising=False)
    from temporal_mcp.config import IdpConfig

    idp = IdpConfig(issuer="https://sso.example.com/realms/demo")
    assert idp.effective_token_url == "https://sso.example.com/realms/demo/protocol/openid-connect/token"


def test_idp_override_wins_over_derivation():
    from temporal_mcp.config import IdpConfig

    idp = IdpConfig(issuer="https://sso.example.com/realms/demo", token_url="https://other/token")
    assert idp.effective_token_url == "https://other/token"


def test_idp_none_issuer_yields_none():
    from temporal_mcp.config import IdpConfig

    idp = IdpConfig()
    assert idp.effective_token_url is None


def test_idp_jwks_uri_field_removed():
    from temporal_mcp.config import IdpConfig

    idp = IdpConfig()
    assert not hasattr(idp, "jwks_uri"), "jwks_uri field must be removed (dead after KeycloakAuthProvider)"
    assert not hasattr(idp, "effective_jwks_uri"), "effective_jwks_uri property must be removed"


def test_mcp_config_has_idp():
    from temporal_mcp.config import IdpConfig, McpServerConfig

    assert isinstance(McpServerConfig().idp, IdpConfig)


def test_ropc_fields_removed():
    from temporal_mcp.config import TemporalConfig

    t = TemporalConfig()
    for gone in ("oidc_username", "oidc_password", "oidc_totp"):
        assert not hasattr(t, gone), f"{gone} must be removed from TemporalConfig"


def test_env_examples_has_idp_anchor_and_no_ropc():
    import pathlib

    text = pathlib.Path("env.examples").read_text(encoding="utf-8")
    assert "IDP_ISSUER=" in text
    assert "sso.example.com" in text
    for banned in ("TEMPORAL_OIDC_USERNAME", "TEMPORAL_OIDC_PASSWORD", "TEMPORAL_OIDC_TOTP"):
        assert banned not in text, f"{banned} must not appear in production env.examples"


def test_auth_mode_defaults_none():
    from temporal_mcp.config import McpServerConfig
    from temporal_mcp.enums import IncomingAuthMode

    assert McpServerConfig().auth_mode == IncomingAuthMode.NONE


def test_auth_mode_env_override(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_MODE", "keycloak")
    from temporal_mcp.config import McpServerConfig
    from temporal_mcp.enums import IncomingAuthMode

    assert McpServerConfig().auth_mode == IncomingAuthMode.KEYCLOAK


def test_removed_incoming_auth_fields_are_gone():
    from temporal_mcp.config import McpServerConfig

    cfg = McpServerConfig()
    for gone in ("auth_client_id", "auth_client_secret", "auth_issuer", "auth_jwks_uri"):
        assert not hasattr(cfg, gone), f"{gone} must be removed"


def test_env_examples_uses_auth_mode_and_no_oidc_proxy_fields():
    import pathlib

    text = pathlib.Path("env.examples").read_text(encoding="utf-8")
    assert "MCP_AUTH_MODE=" in text
    for banned in ("MCP_AUTH_CLIENT_ID", "MCP_AUTH_CLIENT_SECRET", "MCP_AUTH_ISSUER", "MCP_AUTH_JWKS_URI"):
        assert banned not in text, f"{banned} must not appear after the auth-mode rewrite"
