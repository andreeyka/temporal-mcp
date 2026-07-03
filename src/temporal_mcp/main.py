"""Entry point: build and run the Temporal MCP server."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
from typing import TYPE_CHECKING

import truststore
from fastmcp import FastMCP
from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider
from fastmcp.server.transforms.search import BM25SearchTransform

from temporal_mcp.config import McpServerConfig, mcp_config
from temporal_mcp.enums import AuthMode, IncomingAuthMode, TemporalToolTags
from temporal_mcp.errors import IncomingAuthConfigError, MissingAuthVerifierError
from temporal_mcp.middleware import TemporalRpcErrorMiddleware
from temporal_mcp.prompts import prompts_mcp
from temporal_mcp.providers import get_client_pool
from temporal_mcp.resources import resources_mcp
from temporal_mcp.tools.activity_tools import temporal_activity_mcp
from temporal_mcp.tools.batch_tools import temporal_batch_mcp
from temporal_mcp.tools.failure_tools import temporal_failure_mcp
from temporal_mcp.tools.namespace_tools import temporal_namespace_mcp
from temporal_mcp.tools.nexus_tools import temporal_nexus_mcp
from temporal_mcp.tools.schedule_control_tools import temporal_schedule_control_mcp
from temporal_mcp.tools.schedule_tools import temporal_schedule_mcp
from temporal_mcp.tools.task_queue_tools import temporal_task_queue_mcp
from temporal_mcp.tools.worker_deployment_tools import temporal_worker_deployment_mcp
from temporal_mcp.tools.workflow_control_tools import temporal_workflow_control_mcp
from temporal_mcp.tools.workflow_mutate_tools import temporal_workflow_mutate_mcp
from temporal_mcp.tools.workflow_read_tools import temporal_workflow_read_mcp
from temporal_mcp.tools.workflow_rule_tools import temporal_workflow_rule_mcp


if TYPE_CHECKING:
    from collections.abc import AsyncIterator


logger = logging.getLogger(__name__)


def _require_incoming_auth(config: McpServerConfig) -> None:
    """Fail fast when an outbound mode needs a caller token but incoming auth is off.

    Args:
        config: Server configuration.

    Raises:
        MissingAuthVerifierError: If passthrough/exchange is selected with auth_mode=none.
    """
    if config.temporal.auth_mode != AuthMode.SERVICE:
        raise MissingAuthVerifierError(config.temporal.auth_mode.value)


def _resolve_incoming_audience(config: McpServerConfig) -> str | None:
    """Resolve the incoming-JWT audience, enforcing the require-audience policy.

    Args:
        config: Server configuration.

    Returns:
        The audience to validate, or None when validation is deliberately disabled
        via MCP_AUTH_REQUIRE_AUDIENCE=false.

    Raises:
        IncomingAuthConfigError: If no audience is set and MCP_AUTH_REQUIRE_AUDIENCE is true.
    """
    audience = config.auth_audience or config.idp.audience
    if audience:
        return audience
    if config.auth_require_audience:
        raise IncomingAuthConfigError(config.auth_mode.value, "IDP_AUDIENCE")
    logger.warning(
        "keycloak auth: MCP_AUTH_REQUIRE_AUDIENCE=false and no audience configured — "
        "incoming JWT 'aud' validation is DISABLED; tokens minted for other audiences by "
        "this issuer will be accepted (insecure).",
    )
    return None


def _build_keycloak_auth(config: McpServerConfig) -> KeycloakAuthProvider:
    """Build the KeycloakAuthProvider for MCP_AUTH_MODE=keycloak.

    Args:
        config: Server configuration.

    Returns:
        A configured KeycloakAuthProvider.

    Raises:
        IncomingAuthConfigError: If issuer or base_url is missing, or audience is
            missing while MCP_AUTH_REQUIRE_AUDIENCE is true.
    """
    issuer = config.idp.issuer
    if not issuer:
        raise IncomingAuthConfigError(config.auth_mode.value, "IDP_ISSUER")
    if not config.auth_base_url:
        raise IncomingAuthConfigError(config.auth_mode.value, "MCP_AUTH_BASE_URL")
    audience = _resolve_incoming_audience(config)
    # required_scopes=[] intentionally overrides KeycloakAuthProvider's default
    # ["openid"]: the outbound resolver derives the caller subject itself and
    # raises if it is absent, so we do not force an openid scope on callers.
    return KeycloakAuthProvider(
        realm_url=issuer,
        base_url=config.auth_base_url,
        audience=audience,
        required_scopes=[],
    )


def _build_auth(config: McpServerConfig) -> KeycloakAuthProvider | None:
    """Build the incoming-auth provider from the explicit MCP_AUTH_MODE.

    Args:
        config: Server configuration.

    Returns:
        A KeycloakAuthProvider for mode 'keycloak', or None for mode 'none'.

    Raises:
        IncomingAuthConfigError: If mode 'keycloak' is missing a required variable, or the
            auth mode is unrecognized.
        MissingAuthVerifierError: If mode 'none' is paired with passthrough/exchange.
    """
    match config.auth_mode:
        case IncomingAuthMode.NONE:
            _require_incoming_auth(config)
            return None
        case IncomingAuthMode.KEYCLOAK:
            return _build_keycloak_auth(config)
        case _:
            raise IncomingAuthConfigError(str(config.auth_mode), "MCP_AUTH_MODE")


_PROVIDERS = [
    temporal_namespace_mcp,
    temporal_workflow_read_mcp,
    temporal_workflow_mutate_mcp,
    temporal_workflow_control_mcp,
    temporal_failure_mcp,
    temporal_schedule_mcp,
    temporal_schedule_control_mcp,
    temporal_task_queue_mcp,
    temporal_activity_mcp,
    temporal_worker_deployment_mcp,
    temporal_nexus_mcp,
    temporal_workflow_rule_mcp,
    temporal_batch_mcp,
    prompts_mcp,
    resources_mcp,
]


def _build_transforms(config: McpServerConfig) -> list[BM25SearchTransform]:
    """Return the BM25 search transform when tool search is enabled, else none.

    Args:
        config: Server configuration.

    Returns:
        A single-element list with the search transform, or an empty list.
    """
    if not config.tool_search:
        return []
    return [BM25SearchTransform(max_results=8, always_visible=["get_cluster_info", "list_namespaces"])]


@contextlib.asynccontextmanager
async def _lifespan(_app: FastMCP) -> AsyncIterator[None]:
    """Start the client pool (and JWT refresh) for the server lifetime."""
    pool = get_client_pool()
    await pool.start()
    try:
        yield
    finally:
        await pool.close_all()


async def build(config: McpServerConfig = mcp_config) -> FastMCP:
    """Build the FastMCP server with all providers and the pool lifespan.

    Args:
        config: Server configuration.

    Returns:
        A configured FastMCP instance.

    Raises:
        MissingAuthVerifierError: If passthrough/exchange auth is enabled without a JWKS verifier.
    """
    app = FastMCP(
        name=config.server_name,
        mask_error_details=config.mask_error_details,
        auth=_build_auth(config),
        lifespan=_lifespan,
        transforms=_build_transforms(config),
        providers=_PROVIDERS,
        middleware=[TemporalRpcErrorMiddleware()],
    )
    if config.read_only:
        app.disable(tags={TemporalToolTags.MUTATING})
    return app


async def run() -> None:
    """Run the server using the configured transport."""
    app = await build(mcp_config)
    await app.run_async(
        transport=mcp_config.transport.value,
        host=mcp_config.host,
        port=mcp_config.port,
        stateless_http=mcp_config.stateless_http,
    )


def main() -> None:
    """Console-script entry point."""
    # Use the OS trust store (macOS Keychain, Windows cert store, Linux system CAs)
    # so outbound TLS — e.g. the OIDC token endpoint — trusts corporate/private CAs
    # that are not in certifi's bundle. Must run before any SSLContext is created.
    truststore.inject_into_ssl()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run())
    logger.info("Server stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
