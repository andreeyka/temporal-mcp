# Mode: `service`

## Purpose

One shared machine identity is used for every Temporal call, regardless of
which MCP caller made the request. This is the default (`TEMPORAL_AUTH_MODE=service`)
and the simplest mode to operate: it has no dependency on incoming auth being
configured at all.

## What to create in Keycloak

Follow [Keycloak setup](keycloak-setup.md) steps 1–5:

1. Realm `demo`.
2. Note the issuer from the realm's discovery document.
3. A confidential client (`Client authentication: On`) — e.g. `temporal-mcp-svc`.
4. Enable **Service accounts roles: On** on that client; copy its secret from
   the **Credentials** tab.
5. Add an Audience mapper so tokens carry `aud=temporal-api`.

## Required claims/mappers

- `aud` = `temporal-api` (Audience protocol mapper, step 5 above) — required if
  the Temporal frontend enforces audience checks.
- No user-identity claims are needed; this is a client-credentials (machine)
  token, so there is no `sub` representing an end user.

## `.env`

```bash
IDP_ISSUER=https://sso.example.com/realms/demo
IDP_AUDIENCE=temporal-api
TEMPORAL_AUTH_MODE=service
TEMPORAL_OIDC_CLIENT_ID=temporal-mcp-svc
TEMPORAL_OIDC_CLIENT_SECRET=change-me
```

`TEMPORAL_OIDC_TOKEN_URL` is optional — it defaults to the token endpoint
derived from `IDP_ISSUER`. Set `TEMPORAL_OIDC_AUDIENCE` only if this mode's
token needs a different audience than `IDP_AUDIENCE`.

If your cluster instead accepts a static, pre-issued API key rather than OIDC,
skip the client-credentials variables above and set `TEMPORAL_API_KEY` instead.

## How it works

At startup, the server builds a client-credentials token provider
(`make_oidc_token_provider`) from `TEMPORAL_OIDC_*` (falling back to `IDP_*`).
It mints a token via the `client_credentials` grant, attaches it to pooled
Temporal clients, and refreshes it in the background every
`TEMPORAL_OIDC_REFRESH_SECONDS` (default `300`) — trying a `refresh_token`
grant first if the IdP issued one, and falling back to a fresh
`client_credentials` request otherwise. Every caller through the MCP server
shares this one token/identity.

## Verification

1. Start the server: `uv run temporal-mcp`.
2. Call the `get_cluster_info` tool through any MCP client (or `search_tools`
   → `call_tool`). A successful response confirms the service-account token
   was accepted by the Temporal frontend.
3. If it fails with an auth error, check that the Audience mapper is attached
   to the client's token (not just the client scope definition) and that the
   Temporal frontend trusts `IDP_ISSUER`'s JWKS.
