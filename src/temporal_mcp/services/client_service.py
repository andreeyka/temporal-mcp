"""Multi-namespace, multi-identity Temporal client pool.

A high-level Temporal Client binds to one namespace at connect time and carries
one bearer token. With passthrough auth, different callers present different
tokens, so the cache key is (namespace, identity) — not namespace alone. Eviction
drops the reference; the native gRPC channel is released by GC. An asyncio.Lock
guarantees concurrent first-access to a key opens exactly one channel.
"""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from temporalio.client import Client

from temporal_mcp.errors import TemporalConnectionError


if TYPE_CHECKING:
    from temporalio.service import TLSConfig

    from temporal_mcp.services.auth_service import TemporalAuthResolver


logger = logging.getLogger(__name__)

TokenProvider = Callable[[], Awaitable[str]]


class TemporalClientPool:
    """LRU pool of Temporal clients keyed by (namespace, identity)."""

    def __init__(
        self,
        host: str,
        *,
        auth_resolver: TemporalAuthResolver,
        api_key: str | None = None,
        tls: bool | TLSConfig | None = None,
        max_size: int = 64,
        token_provider: TokenProvider | None = None,
        refresh_interval: float = 300.0,
    ) -> None:
        """Initialize the pool.

        Args:
            host: Temporal frontend address.
            auth_resolver: Resolves per-request token + identity.
            api_key: Static service-mode token (optional).
            tls: TLS config or bool; defaults to enabling TLS when a token is set.
            max_size: Maximum cached clients before LRU eviction.
            token_provider: Optional async provider for background JWT refresh.
            refresh_interval: Seconds between background refreshes.
        """
        self._host = host
        self._auth = auth_resolver
        self._api_key = api_key
        self._tls = tls
        self._max = max_size
        self._clients: OrderedDict[tuple[str, str], Client] = OrderedDict()
        self._lock = asyncio.Lock()
        self._token_provider = token_provider
        self._refresh_interval = refresh_interval
        self._refresh_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Prime the service token and start background refresh if configured."""
        if self._token_provider is not None and self._refresh_task is None:
            self._api_key = await self._token_provider()
            self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def _refresh_loop(self) -> None:
        """Periodically refresh the service token and push it to live clients."""
        provider = self._token_provider
        if provider is None:
            return
        while True:
            await asyncio.sleep(self._refresh_interval)
            try:
                token = await provider()
                async with self._lock:
                    self._api_key = token
                    for client in self._clients.values():
                        client.service_client.update_api_key(token)
            except Exception as err:
                logger.warning("service token refresh failed, keeping previous token: %s", err)
                continue

    async def get(self, namespace: str) -> Client:
        """Return a client for ``namespace`` using the current request's identity.

        Args:
            namespace: Target namespace.

        Returns:
            A connected Temporal client (reused when possible).

        Raises:
            TemporalAuthError: If a caller token is required but missing.
            TemporalConnectionError: If connecting to the Temporal frontend fails.
        """
        resolved = await self._auth.resolve_outbound_token(self._api_key)
        key = (namespace, resolved.identity)
        async with self._lock:
            existing = self._clients.get(key)
            if existing is not None:
                self._clients.move_to_end(key)
                if resolved.token is not None:
                    existing.service_client.update_api_key(resolved.token)
                return existing
            try:
                client = await Client.connect(
                    self._host,
                    namespace=namespace,
                    api_key=resolved.token,
                    tls=self._tls if self._tls is not None else (resolved.token is not None),
                )
            except Exception as err:
                raise TemporalConnectionError(self._host, detail=str(err)) from err
            self._clients[key] = client
            if len(self._clients) > self._max:
                self._clients.popitem(last=False)
            return client

    async def bootstrap(self) -> Client:
        """Return a client for cluster-scoped calls (uses the 'default' namespace)."""
        return await self.get("default")

    def __len__(self) -> int:
        """Return the number of cached clients."""
        return len(self._clients)

    async def close_all(self) -> None:
        """Cancel background refresh and drop all cached clients."""
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            self._refresh_task = None
        async with self._lock:
            self._clients.clear()
