"""HTTP probe behavior for container deployments."""

import asyncio

import httpx
import pytest

from temporal_mcp.config import IdpConfig, McpServerConfig
from temporal_mcp.main import build


@pytest.mark.parametrize("auth_mode", ["none", "keycloak"])
def test_health_is_available_without_credentials(auth_mode):
    config = McpServerConfig(
        auth_mode=auth_mode,
        auth_base_url="https://mcp.example.com",
        idp=IdpConfig(issuer="https://sso.example.com/realms/demo", audience="temporal-api"),
    )

    async def scenario():
        server = await build(config)
        transport = httpx.ASGITransport(app=server.http_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    asyncio.run(scenario())
