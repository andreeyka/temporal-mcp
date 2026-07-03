# Mode: `passthrough`

## Purpose

The Temporal frontend sees the *calling MCP user's* identity, not a shared
service identity. The bearer token the caller presented to the MCP server is
forwarded to Temporal unchanged. Use this when Temporal-side audit logs or
authorization must reflect who (or which agent) actually made the call.

`passthrough` requires the [incoming boundary](incoming-sso.md) to be set to
`MCP_AUTH_MODE=keycloak` — the server needs a caller token to forward. If
`TEMPORAL_AUTH_MODE=passthrough` is set while `MCP_AUTH_MODE=none`, the server
raises `MissingAuthVerifierError` at startup and refuses to start.

## What to create in Keycloak

Follow [Keycloak setup](keycloak-setup.md) steps 1–2, then:

3. Create a client that the **MCP client** logs in through using the standard
   OAuth2/OIDC authorization-code flow (this is a different client than the
   machine client used in [service mode](mode-service.md) — it represents
   human/agent end users, not the MCP server itself).
4. Add the same Audience mapper (step 5 of Keycloak setup) to this client, or
   to a client scope it uses, so the tokens it issues carry
   `aud=temporal-api`.

## Required claims/mappers

- `aud` = `temporal-api` — the Temporal frontend must be configured to accept
  this audience.
- `iss` must match `IDP_ISSUER` — Temporal must trust the same issuer/JWKS the
  MCP server verifies incoming tokens against.
- A `sub` claim identifying the caller (used as the Temporal client-pool cache
  key so different callers don't share a pooled gRPC client).

## `.env`

```bash
MCP_AUTH_MODE=keycloak
IDP_ISSUER=https://sso.example.com/realms/demo
IDP_AUDIENCE=temporal-api
MCP_AUTH_BASE_URL=https://mcp.example.com
TEMPORAL_AUTH_MODE=passthrough
```

See [incoming-sso.md](incoming-sso.md) for the full incoming-auth
configuration this depends on.

## How it works

On every Temporal call, the server reads the caller's validated access token
(`get_access_token()`), takes its `subject` (or `sub`/`client_id` claim) as the
cache identity, and forwards `access.token` to Temporal as-is — no additional
network round-trip. If no caller token is present, the call fails with an auth
error rather than silently falling back to a service identity.

## Verification

1. Configure incoming auth per [incoming-sso.md](incoming-sso.md) and start
   the server.
2. Authenticate an MCP client against the issuer above so it holds a valid
   access token.
3. Call any namespace-scoped tool (e.g. `list_workflows`). A successful
   response means Temporal accepted the caller's own token; check Temporal's
   audit/access logs to confirm the request identity matches the caller's
   `sub`, not a shared service account.
