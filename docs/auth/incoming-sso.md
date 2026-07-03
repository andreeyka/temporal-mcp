# Incoming auth / SSO

This is the boundary between the MCP client and this server: who is allowed to
call it, and how do they prove their identity? It is independent of the
[outbound mode](README.md#outbound-mode-matrix) the server uses to talk to
Temporal.

The server builds its incoming-auth provider (`_build_auth` in `main.py`) from
a single explicit setting, `MCP_AUTH_MODE`:

| Mode | Behavior |
| --- | --- |
| `none` (default) | No incoming auth. Every request is accepted unauthenticated. |
| `keycloak` | The server verifies every incoming JWT via FastMCP's `KeycloakAuthProvider` and advertises OAuth protected-resource metadata so compliant clients can log in. |

## Mode: `none`

No token is required or checked. Use this only for local development, or when
an external layer (reverse proxy, API gateway, or service-mesh authentication
layer) already terminates SSO and restricts network access to the server —
in that topology the server trusts the network path rather than verifying
tokens itself, so make sure that boundary is actually enforced.

`none` cannot be combined with `TEMPORAL_AUTH_MODE=passthrough` or `exchange`:
both need a caller token to forward or exchange, and the server has none to
offer. Selecting either without `MCP_AUTH_MODE=keycloak` raises
`MissingAuthVerifierError` at startup.

## Mode: `keycloak`

SSO is **client-initiated**: MCP clients discover the Keycloak realm
themselves and log in on their own, rather than the server driving an OAuth
flow on their behalf. Concretely:

- The server advertises OAuth protected-resource metadata per
  [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728) at
  `MCP_AUTH_BASE_URL`. Compliant MCP clients (e.g. Claude Code) discover the
  SSO issuer from this metadata and run the authorization-code flow
  themselves, then present the resulting access token as a bearer token on
  every request.
- The server never runs an OAuth flow, never holds a client secret for this
  purpose, and never redirects anyone. It only validates each incoming JWT
  against the configured issuer, audience, and JWKS via FastMCP's
  `KeycloakAuthProvider`.

Required configuration:

```bash
MCP_AUTH_MODE=keycloak
IDP_ISSUER=https://sso.example.com/realms/demo
MCP_AUTH_BASE_URL=https://mcp.example.com
IDP_AUDIENCE=temporal-api                # or MCP_AUTH_AUDIENCE for a per-task override
```

`IDP_ISSUER`, `MCP_AUTH_BASE_URL`, and an audience (`IDP_AUDIENCE` or
`MCP_AUTH_AUDIENCE`) are all required by default — the server raises
`IncomingAuthConfigError` at startup if any is missing while
`MCP_AUTH_MODE=keycloak`. `MCP_AUTH_AUDIENCE` is a per-task override and falls
back to `IDP_AUDIENCE` when unset.

To run without an audience, set `MCP_AUTH_REQUIRE_AUDIENCE=false` (default
`true`). This is an **insecure** escape hatch: the incoming JWT `aud` claim is
no longer validated, so any correctly-signed, unexpired token from the same
issuer is accepted regardless of the audience it was minted for — including
tokens issued for other clients/resources. The server logs a prominent startup
warning whenever audience validation is disabled. Prefer configuring a Keycloak
Audience mapper (see [keycloak-setup.md](keycloak-setup.md)) so tokens carry the
right `aud` and validation can stay on.

## Required claims

When `MCP_AUTH_MODE=keycloak`, the incoming JWT must satisfy:

- `iss` matching `IDP_ISSUER`.
- `aud` matching `MCP_AUTH_AUDIENCE` (or `IDP_AUDIENCE` when unset).
- A valid signature verifiable against the issuer's JWKS.

If you plan to use [`passthrough`](mode-passthrough.md) or
[`exchange`](mode-exchange.md) outbound mode, the token also needs a `sub`
claim (or a resolvable `client_id`) so the server can key its per-caller
Temporal client cache.

## Verification

1. Set the `.env` block for your chosen mode and start the server.
2. For `keycloak`, call any tool from an authenticated MCP client. An
   unauthenticated request should be rejected (401/403); an authenticated one
   should succeed.
3. For `keycloak`, confirm the server's `/.well-known/oauth-protected-resource`
   endpoint is reachable by clients and advertises `MCP_AUTH_BASE_URL` as the
   resource and `IDP_ISSUER` as the authorization server.
