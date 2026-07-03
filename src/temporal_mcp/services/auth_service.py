"""Resolve the bearer token + cache identity for an outbound Temporal call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp.server.dependencies import get_access_token

from temporal_mcp.enums import AuthMode
from temporal_mcp.errors import TemporalAuthError, TokenExchangeError
from temporal_mcp.errors.messages import (
    MSG_AUTH_NO_SUBJECT,
    MSG_AUTH_NO_TOKEN,
    MSG_AUTH_UNKNOWN_MODE,
    MSG_AUTH_WRONG_TOKEN_TYPE,
)


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from temporal_mcp.config import IdpConfig, TemporalConfig


@dataclass(frozen=True)
class ResolvedToken:
    """Outbound token and the cache-partition identity."""

    token: str | None
    identity: str


class TemporalAuthResolver:
    """Resolves outbound tokens according to the configured auth mode."""

    def __init__(self, config: TemporalConfig, idp: IdpConfig) -> None:
        """Initialize with Temporal and shared IdP configuration.

        Args:
            config: Temporal connection/auth configuration.
            idp: Shared identity-provider anchor (issuer/audience/endpoints).
        """
        self._config = config
        self._idp = idp

    async def resolve_outbound_token(self, service_token: str | None) -> ResolvedToken:
        """Resolve the token + identity for the current request.

        Args:
            service_token: The pool's current machine token (service mode only).

        Returns:
            The token to present to Temporal plus the cache identity.

        Raises:
            TemporalAuthError: If a caller token is required but missing, lacks a
                derivable subject, carries a non-access `typ` claim, or the auth
                mode is unknown.
            TokenExchangeError: If RFC 8693 exchange fails.
        """
        mode = self._config.auth_mode
        if mode == AuthMode.SERVICE:
            return ResolvedToken(token=service_token, identity="")

        access = get_access_token()
        if access is None or not access.token:
            raise TemporalAuthError(MSG_AUTH_NO_TOKEN)
        subject = access.subject or access.claims.get("sub") or access.client_id
        if not subject:
            raise TemporalAuthError(MSG_AUTH_NO_SUBJECT)

        token_type = access.claims.get("typ")
        if token_type is not None and token_type != "Bearer":  # noqa: S105
            raise TemporalAuthError(MSG_AUTH_WRONG_TOKEN_TYPE.format(typ=token_type))

        if mode == AuthMode.PASSTHROUGH:
            return ResolvedToken(token=access.token, identity=subject)
        if mode == AuthMode.EXCHANGE:
            return ResolvedToken(token=await self._exchange(access.token), identity=subject)
        raise TemporalAuthError(MSG_AUTH_UNKNOWN_MODE.format(mode=mode))

    async def _exchange(self, subject_token: str) -> str:
        """Swap the caller's token for a Temporal-audience token (RFC 8693).

        Args:
            subject_token: The caller's incoming bearer token.

        Returns:
            The exchanged access token.

        Raises:
            TokenExchangeError: If the exchange endpoint fails or returns no token.
        """
        cfg = self._config
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": subject_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": cfg.exchange_audience or self._idp.audience or "",
            "client_id": cfg.exchange_client_id.get_secret_value(),
            "client_secret": cfg.exchange_client_secret.get_secret_value(),
        }
        if cfg.exchange_scope:
            data["scope"] = cfg.exchange_scope
        token_url = cfg.exchange_token_url or self._idp.effective_token_url
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                return await _fetch_access_token(http, token_url or "", data)
        except TokenExchangeError:
            raise
        except Exception as err:
            raise TokenExchangeError(detail=str(err)) from err


async def _post_token(http: httpx.AsyncClient, url: str, data: dict[str, str]) -> dict[str, Any]:
    """POST form data to an OAuth token endpoint and return the parsed JSON body.

    Args:
        http: The async HTTP client to use.
        url: The token endpoint URL.
        data: Form fields to send.

    Returns:
        The parsed JSON response body.

    Raises:
        TokenExchangeError: If the endpoint does not respond with HTTP 200.
    """
    resp = await http.post(url, data=data)
    if resp.status_code != httpx.codes.OK:
        raise TokenExchangeError(detail=f"{resp.status_code} {getattr(resp, 'text', '')[:200]}")
    return resp.json()


async def _fetch_access_token(http: httpx.AsyncClient, url: str, data: dict[str, str]) -> str:
    """POST to an OAuth token endpoint and return its access_token, raising if absent.

    Args:
        http: The async HTTP client to use.
        url: The token endpoint URL.
        data: Form fields to send.

    Returns:
        The access token from the response.

    Raises:
        TokenExchangeError: If the endpoint fails or the response carries no access_token.
    """
    body = await _post_token(http, url, data)
    token = body.get("access_token")
    if not token:
        raise TokenExchangeError(detail="response had no access_token")
    return str(token)


def make_oidc_token_provider(config: TemporalConfig, idp: IdpConfig) -> Callable[[], Awaitable[str]] | None:
    """Build a client-credentials OIDC token provider, or None if not configured.

    Mints a fresh access token via the OAuth2 client-credentials grant on every
    call. Client-credentials grants do not return refresh tokens with Keycloak,
    so there is no refresh round-trip to maintain. Returns None when no
    effective token URL is configured.

    Args:
        config: Temporal configuration (client id/secret, optional scope/audience/token URL).
        idp: Shared identity-provider anchor (default token URL/audience).

    Returns:
        An async callable returning a fresh access token, or None.
    """
    token_url = config.oidc_token_url or idp.effective_token_url
    if not token_url:
        return None

    client_auth = {
        "client_id": config.oidc_client_id.get_secret_value(),
        "client_secret": config.oidc_client_secret.get_secret_value(),
    }

    async def provider() -> str:
        data = {**client_auth, "grant_type": "client_credentials"}
        if config.oidc_scope:
            data["scope"] = config.oidc_scope
        audience = config.oidc_audience or idp.audience
        if audience:
            data["audience"] = audience
        async with httpx.AsyncClient(timeout=10.0) as http:
            return await _fetch_access_token(http, token_url, data)

    return provider
