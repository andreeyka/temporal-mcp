# Mode: `exchange`

## Purpose

Like [`passthrough`](mode-passthrough.md), Temporal sees the calling MCP
user's identity — but instead of forwarding the caller's raw token, the server
exchanges it per request for a token scoped to Temporal, using
[RFC 8693 OAuth 2.0 Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693).
Use this when the caller's token isn't directly acceptable to Temporal (wrong
audience, too broad a scope, or issued for a different resource) but your
identity provider can mint a narrower, Temporal-audience token on its behalf.

Like `passthrough`, `exchange` requires the [incoming boundary](incoming-sso.md)
to be configured with a token verifier — the server raises
`MissingAuthVerifierError` at startup otherwise, since there is no caller
token to exchange.

## What to create in Keycloak

Follow [Keycloak setup](keycloak-setup.md) steps 1–2, then:

3. Enable **token exchange** for the realm/client — in Keycloak this is a
   feature flag (`token-exchange`) that must be turned on for the target
   client before it will honor `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`
   requests. Consult your Keycloak version's admin console/documentation for
   the exact toggle location, as this has moved across releases.
4. Create (or reuse) a confidential client dedicated to performing the
   exchange, e.g. `temporal-mcp-exchange`, with **Client authentication: On**.
5. Authorize that client as an allowed "exchanger" for the audience/client
   that issued the caller's original token — Keycloak requires the exchange
   client to be explicitly permitted to exchange tokens issued to another
   client.
6. Add the Audience mapper (Keycloak setup step 5) so exchanged tokens carry
   `aud=temporal-api`.

## Required claims/mappers

- The caller's original token: any `iss`/`aud` acceptable to the incoming
  verifier (`IDP_*` / `MCP_AUTH_*`).
- The exchanged token: `aud=temporal-api` and `iss` trusted by the Temporal
  frontend, same as [passthrough](mode-passthrough.md).

## `.env`

```bash
MCP_AUTH_MODE=keycloak
IDP_ISSUER=https://sso.example.com/realms/demo
IDP_AUDIENCE=temporal-api
MCP_AUTH_BASE_URL=https://mcp.example.com
TEMPORAL_AUTH_MODE=exchange
TEMPORAL_EXCHANGE_CLIENT_ID=temporal-mcp-exchange
TEMPORAL_EXCHANGE_CLIENT_SECRET=change-me
```

`TEMPORAL_EXCHANGE_TOKEN_URL` and `TEMPORAL_EXCHANGE_AUDIENCE`/`TEMPORAL_EXCHANGE_SCOPE`
are optional overrides; they default to the token URL/audience derived from
`IDP_*`.

## How it works

On every Temporal call, the server takes the caller's validated access token
and POSTs a standard token-exchange request to the token endpoint:

```
grant_type=urn:ietf:params:oauth:grant-type:token-exchange
subject_token=<caller's access token>
subject_token_type=urn:ietf:params:oauth:token-type:access_token
audience=temporal-api
client_id=temporal-mcp-exchange
client_secret=...
```

The returned `access_token` is what gets sent to Temporal. If the exchange
fails or the response has no `access_token`, the call fails with a
`TokenExchangeError` rather than falling back to any other identity. This adds
one extra network round-trip per Temporal call compared to `passthrough`.

## Verification

1. Configure incoming auth and enable token exchange in Keycloak.
2. Start the server with the `.env` block above.
3. Authenticate an MCP client and call a namespace-scoped tool.
4. A successful response confirms the exchange succeeded; on failure, check
   the server logs for `TokenExchangeError` and confirm the exchange client is
   authorized to exchange tokens for the caller's original client/audience.
