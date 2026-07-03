"""Tests for the Temporal auth resolver service."""

import asyncio

import pytest

from temporal_mcp.config import IdpConfig, TemporalConfig
from temporal_mcp.enums import AuthMode
from temporal_mcp.errors import TemporalAuthError
from temporal_mcp.services import auth_service as auth


class _FakeAccess:
    def __init__(self, token, sub):
        self.token = token
        self.subject = sub
        self.claims = {}
        self.client_id = "cid"


def _resolver(mode):
    return auth.TemporalAuthResolver(TemporalConfig(auth_mode=mode), IdpConfig())


def test_service_mode_uses_service_token():
    r = asyncio.run(_resolver(AuthMode.SERVICE).resolve_outbound_token("svc-tok"))
    assert r.token == "svc-tok"
    assert r.identity == ""


def test_passthrough_uses_caller_token(monkeypatch):
    monkeypatch.setattr(auth, "get_access_token", lambda: _FakeAccess("tok-alice", "alice"))
    r = asyncio.run(_resolver(AuthMode.PASSTHROUGH).resolve_outbound_token(None))
    assert r.token == "tok-alice"
    assert r.identity == "alice"


def test_passthrough_missing_token_raises(monkeypatch):
    monkeypatch.setattr(auth, "get_access_token", lambda: None)
    with pytest.raises(TemporalAuthError):
        asyncio.run(_resolver(AuthMode.PASSTHROUGH).resolve_outbound_token(None))


def test_passthrough_no_subject_raises(monkeypatch):
    class _NoSubjectAccess:
        def __init__(self):
            self.token = "tok-no-subject"
            self.subject = None
            self.claims = {}
            self.client_id = None

    monkeypatch.setattr(auth, "get_access_token", _NoSubjectAccess)
    with pytest.raises(TemporalAuthError):
        asyncio.run(_resolver(AuthMode.PASSTHROUGH).resolve_outbound_token(None))


def test_passthrough_rejects_refresh_token(monkeypatch):
    access = _FakeAccess("tok-refresh", "alice")
    access.claims = {"typ": "Refresh"}
    monkeypatch.setattr(auth, "get_access_token", lambda: access)
    with pytest.raises(TemporalAuthError):
        asyncio.run(_resolver(AuthMode.PASSTHROUGH).resolve_outbound_token(None))


def test_passthrough_accepts_bearer_token(monkeypatch):
    access = _FakeAccess("tok-alice", "alice")
    access.claims = {"typ": "Bearer"}
    monkeypatch.setattr(auth, "get_access_token", lambda: access)
    r = asyncio.run(_resolver(AuthMode.PASSTHROUGH).resolve_outbound_token(None))
    assert r.token == "tok-alice"


def test_provider_none_without_token_url():
    provider = auth.make_oidc_token_provider(TemporalConfig(_env_file=None), IdpConfig(_env_file=None))
    assert provider is None


def test_provider_client_credentials_uses_effective_token_url(monkeypatch):
    captured = {}

    class _Resp:
        status_code = 200

        def json(self):
            return {"access_token": "cc-token"}

        def raise_for_status(self):
            pass

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, data=None):
            captured["url"] = url
            captured["grant"] = data["grant_type"]
            return _Resp()

    monkeypatch.setattr(auth.httpx, "AsyncClient", _Client)
    idp = IdpConfig(issuer="https://sso.example.com/realms/demo", _env_file=None)
    provider = auth.make_oidc_token_provider(TemporalConfig(oidc_client_id="svc", _env_file=None), idp)
    assert provider is not None
    token = asyncio.run(provider())
    assert token == "cc-token"
    assert captured["url"] == "https://sso.example.com/realms/demo/protocol/openid-connect/token"
    assert captured["grant"] == "client_credentials"


def test_client_credentials_provider_has_no_refresh_roundtrip(monkeypatch):
    calls = []

    class _Resp:
        status_code = 200

        def json(self):
            return {"access_token": "cc-token", "refresh_token": "rt"}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, data=None):
            calls.append(data["grant_type"])
            return _Resp()

    monkeypatch.setattr(auth.httpx, "AsyncClient", _Client)
    idp = IdpConfig(issuer="https://sso.example.com/realms/demo", _env_file=None)
    provider = auth.make_oidc_token_provider(TemporalConfig(oidc_client_id="svc", _env_file=None), idp)
    assert asyncio.run(provider()) == "cc-token"
    assert asyncio.run(provider()) == "cc-token"
    # every mint is client_credentials — a refresh token is never redeemed
    assert calls == ["client_credentials", "client_credentials"]


def test_make_oidc_provider_raises_on_non_200(monkeypatch):
    class _Resp:
        status_code = 400
        text = "bad"

        def json(self):
            return {}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, data=None):
            return _Resp()

    monkeypatch.setattr(auth.httpx, "AsyncClient", _Client)
    idp = IdpConfig(issuer="https://sso.example.com/realms/demo", _env_file=None)
    provider = auth.make_oidc_token_provider(TemporalConfig(oidc_client_id="svc", _env_file=None), idp)
    with pytest.raises(auth.TokenExchangeError):
        asyncio.run(provider())


def test_exchange_non_200_single_error_prefix(monkeypatch):
    access = _FakeAccess("tok-alice", "alice")
    access.claims = {"typ": "Bearer"}
    monkeypatch.setattr(auth, "get_access_token", lambda: access)

    class _Resp:
        status_code = 400
        text = "bad"

        def json(self):
            return {}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, data=None):
            return _Resp()

    monkeypatch.setattr(auth.httpx, "AsyncClient", _Client)
    resolver = auth.TemporalAuthResolver(
        TemporalConfig(
            auth_mode=AuthMode.EXCHANGE,
            exchange_token_url="https://sso.example.com/token",
            _env_file=None,
        ),
        IdpConfig(_env_file=None),
    )
    with pytest.raises(auth.TokenExchangeError) as exc:
        asyncio.run(resolver.resolve_outbound_token(None))
    assert str(exc.value).count("Token exchange failed") == 1
