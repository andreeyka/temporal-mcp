import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from temporal_mcp.config import IdpConfig, TemporalConfig
from temporal_mcp.enums import AuthMode
from temporal_mcp.errors import TemporalAuthError
from temporal_mcp.services import auth_service as auth, client_service as poolmod


def _service_resolver():
    return auth.TemporalAuthResolver(TemporalConfig(auth_mode=AuthMode.SERVICE), IdpConfig())


def _connect_factory(calls):
    async def fake_connect(host, *, namespace, api_key=None, tls=None):
        calls.append(namespace)
        m = AsyncMock(name=f"client[{namespace}]")
        m.service_client = MagicMock()
        m._ns, m._tok = namespace, api_key
        return m

    return fake_connect


def test_cache_hit_no_reconnect():
    calls = []
    with patch.object(poolmod.Client, "connect", side_effect=_connect_factory(calls)):
        p = poolmod.TemporalClientPool("h", auth_resolver=_service_resolver(), max_size=3)
        a = asyncio.run(p.get("ns-a"))
        a2 = asyncio.run(p.get("ns-a"))
        assert a is a2
        assert calls == ["ns-a"]


def test_lru_eviction_and_reconnect():
    calls = []
    with patch.object(poolmod.Client, "connect", side_effect=_connect_factory(calls)):
        p = poolmod.TemporalClientPool("h", auth_resolver=_service_resolver(), max_size=3)

        async def scenario():
            await p.get("ns-a")
            await p.get("ns-b")
            await p.get("ns-c")
            await p.get("ns-a")
            await p.get("ns-d")
            keys = {ns for (ns, _ident) in p._clients}
            assert keys == {"ns-c", "ns-a", "ns-d"}
            before = len(calls)
            await p.get("ns-b")
            assert len(calls) == before + 1

        asyncio.run(scenario())


def test_concurrent_single_connect():
    calls = []
    with patch.object(poolmod.Client, "connect", side_effect=_connect_factory(calls)):
        p = poolmod.TemporalClientPool("h", auth_resolver=_service_resolver(), max_size=8)

        async def scenario():
            await asyncio.gather(*[p.get("ns-race") for _ in range(20)])
            assert calls.count("ns-race") == 1

        asyncio.run(scenario())


def test_users_get_isolated_channels():
    resolver = auth.TemporalAuthResolver(TemporalConfig(auth_mode=AuthMode.PASSTHROUGH), IdpConfig())

    class _Access:
        def __init__(self, token, sub):
            self.token, self.subject, self.claims, self.client_id = token, sub, {}, "cid"

    calls = []
    with patch.object(poolmod.Client, "connect", side_effect=_connect_factory(calls)):
        p = poolmod.TemporalClientPool("h", auth_resolver=resolver, max_size=8)

        async def scenario():
            with patch.object(auth, "get_access_token", return_value=_Access("tok-alice", "alice")):
                ca = await p.get("ns-a")
                assert ca._tok == "tok-alice"
            with patch.object(auth, "get_access_token", return_value=_Access("tok-bob", "bob")):
                cb = await p.get("ns-a")
                assert cb._tok == "tok-bob"
            assert ca is not cb
            assert len(p) == 2
            with patch.object(auth, "get_access_token", return_value=_Access("tok-alice-2", "alice")):
                ca2 = await p.get("ns-a")
            assert ca2 is ca
            ca.service_client.update_api_key.assert_called_with("tok-alice-2")

        asyncio.run(scenario())


def test_missing_caller_token_raises():
    resolver = auth.TemporalAuthResolver(TemporalConfig(auth_mode=AuthMode.PASSTHROUGH), IdpConfig())
    with patch.object(poolmod.Client, "connect", side_effect=_connect_factory([])):
        p = poolmod.TemporalClientPool("h", auth_resolver=resolver)
        with patch.object(auth, "get_access_token", return_value=None), pytest.raises(TemporalAuthError):
            asyncio.run(p.get("ns-a"))


def test_jwt_refresh_pushes_to_live_clients():
    counter = {"n": 0}

    async def provider():
        counter["n"] += 1
        return f"jwt-{counter['n']}"

    calls = []

    async def scenario():
        with patch.object(poolmod.Client, "connect", side_effect=_connect_factory(calls)):
            p = poolmod.TemporalClientPool(
                "h",
                auth_resolver=_service_resolver(),
                token_provider=provider,
                refresh_interval=0.05,
            )
            await p.start()
            a = await p.get("ns-a")
            assert a._tok == "jwt-1"
            await asyncio.sleep(0.08)
            a.service_client.update_api_key.assert_called_with("jwt-2")
            await p.close_all()
            assert p._refresh_task is None

    asyncio.run(scenario())


def test_refresh_loop_logs_on_failure(caplog):
    import asyncio
    import logging

    from temporal_mcp.services.client_service import TemporalClientPool

    class _Resolver:
        async def resolve_outbound_token(self, service_token):
            raise AssertionError("not used in this test")

    calls = {"n": 0}

    async def failing_provider():
        calls["n"] += 1
        raise RuntimeError("token endpoint down")

    async def scenario():
        pool = TemporalClientPool(
            "localhost:7233",
            auth_resolver=_Resolver(),
            token_provider=failing_provider,
            refresh_interval=0.01,
        )
        # prime() calls the provider once directly; start the loop and let it tick
        pool._refresh_task = asyncio.ensure_future(pool._refresh_loop())
        await asyncio.sleep(0.05)
        pool._refresh_task.cancel()

    with caplog.at_level(logging.WARNING):
        asyncio.run(scenario())
    assert any("refresh" in r.message.lower() for r in caplog.records)


def test_get_wraps_connect_failure(monkeypatch):
    import asyncio

    from temporalio.client import Client

    from temporal_mcp.errors import TemporalConnectionError
    from temporal_mcp.services.client_service import TemporalClientPool

    class _Resolver:
        async def resolve_outbound_token(self, service_token):
            from temporal_mcp.services.auth_service import ResolvedToken

            return ResolvedToken(token="t", identity="id")

    async def _boom(*a, **k):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(Client, "connect", _boom)
    pool = TemporalClientPool("localhost:7233", auth_resolver=_Resolver())
    with pytest.raises(TemporalConnectionError):
        asyncio.run(pool.get("default"))
