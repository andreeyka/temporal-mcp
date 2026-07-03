"""Client-pool singleton provider."""

from __future__ import annotations

from functools import lru_cache

from fastmcp.dependencies import Depends

from temporal_mcp.config import mcp_config
from temporal_mcp.enums import AuthMode
from temporal_mcp.services.auth_service import TemporalAuthResolver, make_oidc_token_provider
from temporal_mcp.services.client_service import TemporalClientPool


@lru_cache(maxsize=1)
def get_client_pool() -> TemporalClientPool:
    """Build (once) and return the shared Temporal client pool.

    The client-credentials token provider is only wired in ``service`` mode;
    ``passthrough``/``exchange`` derive their outbound token per request from the
    caller's identity, so priming a machine token at startup is both unnecessary
    and would fail when no service-account credentials are configured.

    Returns:
        The cached TemporalClientPool built from configuration.
    """
    temporal = mcp_config.temporal
    idp = mcp_config.idp
    api_key = temporal.api_key.get_secret_value() or None
    token_provider = make_oidc_token_provider(temporal, idp) if temporal.auth_mode == AuthMode.SERVICE else None
    return TemporalClientPool(
        temporal.host,
        auth_resolver=TemporalAuthResolver(temporal, idp),
        api_key=api_key,
        tls=temporal.tls,
        max_size=temporal.pool_max,
        token_provider=token_provider,
        refresh_interval=temporal.oidc_refresh_seconds,
    )


TemporalClientPoolProvider = Depends(get_client_pool)
