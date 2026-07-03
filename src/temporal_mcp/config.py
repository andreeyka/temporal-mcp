"""Server and Temporal configuration (pydantic-settings)."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from temporal_mcp.enums import AuthMode, IncomingAuthMode, TransportType


class IdpConfig(BaseSettings):
    """Shared identity-provider anchor (typically a Keycloak realm).

    Declares the issuer once; the token endpoint is derived from it by Keycloak
    convention and may be overridden for split deployments. The JWKS endpoint is
    derived internally by FastMCP's `KeycloakAuthProvider` from the issuer and is
    not configurable here.
    """

    model_config = SettingsConfigDict(
        env_prefix="IDP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    issuer: str | None = Field(default=None, description="IdP issuer / realm base URL")
    audience: str | None = Field(default=None, description="Default token audience")
    token_url: str | None = Field(default=None, description="Override token URL (else derived)")

    @property
    def effective_token_url(self) -> str | None:
        """Return the override token URL, else derive it from the issuer."""
        if self.token_url:
            return self.token_url
        return f"{self.issuer.rstrip('/')}/protocol/openid-connect/token" if self.issuer else None


class TemporalConfig(BaseSettings):
    """Temporal connection and auth configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TEMPORAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    host: str = Field(default="localhost:7233", description="Temporal frontend address")
    tls: bool | None = Field(
        default=None,
        description="TLS to the Temporal frontend; unset = auto (on when a token is present)",
    )
    auth_mode: AuthMode = Field(default=AuthMode.SERVICE, description="Outbound auth mode")
    api_key: SecretStr = Field(default=SecretStr(""), description="Static API key (service mode)")
    pool_max: int = Field(default=64, description="Max cached (namespace, identity) clients", ge=1)

    oidc_token_url: str | None = Field(default=None, description="OIDC client-credentials token URL")
    oidc_client_id: SecretStr = Field(default=SecretStr(""), description="OIDC client id")
    oidc_client_secret: SecretStr = Field(default=SecretStr(""), description="OIDC client secret")
    oidc_scope: str | None = Field(default=None, description="OIDC scope")
    oidc_audience: str | None = Field(default=None, description="OIDC audience")
    oidc_refresh_seconds: float = Field(default=300.0, description="Background JWT refresh interval", gt=0)

    exchange_token_url: str | None = Field(default=None, description="RFC 8693 token-exchange endpoint")
    exchange_audience: str | None = Field(default=None, description="Target audience (Temporal)")
    exchange_scope: str | None = Field(default=None, description="Exchange scope")
    exchange_client_id: SecretStr = Field(default=SecretStr(""), description="Exchange client id")
    exchange_client_secret: SecretStr = Field(default=SecretStr(""), description="Exchange client secret")


class McpServerConfig(BaseSettings):
    """Top-level MCP server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    server_name: str = Field(default="temporal-multi-namespace", description="MCP server name")
    mask_error_details: bool = Field(default=True, description="Hide internal error details")
    host: str = Field(default="0.0.0.0", description="Bind host")  # noqa: S104
    port: int = Field(default=8000, description="Bind port")
    transport: TransportType = Field(default=TransportType.HTTP, description="MCP transport")
    stateless_http: bool = Field(default=True, description="Stateless HTTP mode")
    read_only: bool = Field(default=False, description="Expose only read-only tools (hide mutations)")
    tool_search: bool = Field(
        default=True,
        description="Expose tools through BM25 search (search_tools/call_tool) instead of the full catalog",
    )

    auth_mode: IncomingAuthMode = Field(
        default=IncomingAuthMode.NONE,
        description="Incoming MCP auth: 'none' or 'keycloak' (RFC 9728 client-initiated SSO)",
    )
    auth_audience: str | None = Field(default=None, description="Expected audience of incoming JWTs")
    auth_base_url: str | None = Field(
        default=None,
        description="Public base URL of this MCP server: enables OAuth protected-resource "
        "metadata (RFC 9728) so MCP clients can discover the SSO issuer and log in themselves",
    )
    auth_require_audience: bool = Field(
        default=True,
        description="Require and validate the incoming JWT 'aud' claim in keycloak mode. "
        "Set false only to deliberately run without audience validation (insecure).",
    )

    idp: IdpConfig = Field(default_factory=IdpConfig, description="Shared identity-provider anchor")
    temporal: TemporalConfig = Field(default_factory=TemporalConfig, description="Temporal configuration")


def get_mcp_server_config() -> McpServerConfig:
    """Build the MCP server configuration from the environment.

    Returns:
        A populated McpServerConfig instance.
    """
    return McpServerConfig()


mcp_config = get_mcp_server_config()
