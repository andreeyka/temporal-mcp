# Authentication guide

The server has two independent auth boundaries. Configuring one does not configure
the other — read both sections before deploying.

| Boundary | Direction | Question it answers | Config prefix |
| --- | --- | --- | --- |
| **Incoming** | MCP client → this server | "Who is calling the MCP server, and is their token valid?" | `MCP_AUTH_MODE` (+ `MCP_AUTH_BASE_URL`/`MCP_AUTH_AUDIENCE`, shared `IDP_*`) |
| **Outbound** | This server → Temporal frontend | "What identity does the server present to Temporal?" | `TEMPORAL_AUTH_MODE` + `TEMPORAL_OIDC_*` / `TEMPORAL_EXCHANGE_*` (+ shared `IDP_*`) |

Both boundaries fall back to the same `IDP_*` anchor (issuer, audience, and a
derived token endpoint) so a single identity provider configuration can drive
both sides. See [Incoming auth / SSO](incoming-sso.md) for the incoming boundary.

`MCP_AUTH_MODE` selects the incoming boundary:

| Mode | Behavior |
| --- | --- |
| `none` (default) | The server accepts every request unauthenticated. Only safe for local development or when an external layer (gateway/service mesh) already restricts access. |
| `keycloak` | The server advertises OAuth protected-resource metadata (RFC 9728) and verifies every incoming JWT via FastMCP's `KeycloakAuthProvider`. Requires `IDP_ISSUER`, `MCP_AUTH_BASE_URL`, and `IDP_AUDIENCE` (or `MCP_AUTH_AUDIENCE`). Set `MCP_AUTH_REQUIRE_AUDIENCE=false` to run without `aud` validation — insecure; see [incoming-sso.md](incoming-sso.md). |

When `MCP_AUTH_MODE=keycloak`, set `MCP_AUTH_CLAIM_EXPR` to add an
authorization check after signature, issuer, and audience validation. This is
useful for Keycloak group allowlists such as `"Example-Admins" in groups ||
"Example-Operators" in groups`; it does not replace `aud` validation. A valid
JWT that fails the expression is rejected at the MCP authorization layer, not as
an invalid token.

## Outbound mode matrix

`TEMPORAL_AUTH_MODE` selects how the server authenticates to the Temporal frontend:

| Mode | Identity presented to Temporal | Mechanism | Guide |
| --- | --- | --- | --- |
| `service` (default) | One shared machine identity for every caller | Static API key, or an OAuth2 client-credentials token fetched and rotated by the server | [mode-service.md](mode-service.md) |
| `passthrough` | The calling MCP user's own identity | The caller's incoming bearer token is forwarded to Temporal unchanged | [mode-passthrough.md](mode-passthrough.md) |
| `exchange` | The calling MCP user's identity, on a Temporal-scoped token | The caller's token is exchanged per-request for a Temporal-audience token (RFC 8693) | [mode-exchange.md](mode-exchange.md) |

## How to choose

- Only need one Temporal identity for all traffic, no per-user audit trail required
  → **`service`**.
- Need Temporal-side audit logs / authorization to reflect the calling human or
  agent, and Temporal can be configured to trust the same issuer/JWKS as the MCP
  server → **`passthrough`**.
- Need per-user identity but Temporal must see a token scoped/audienced
  specifically for it (different audience, shorter lifetime, or a different
  issuer than the one the MCP client authenticated against) and your identity
  provider supports token exchange → **`exchange`**.
- Unsure, or bootstrapping a new deployment → start with **`service`**, verify
  the server can reach Temporal, then move to `passthrough`/`exchange` once
  incoming auth is configured and verified.

Both `passthrough` and `exchange` **require** the incoming boundary to be set
to `MCP_AUTH_MODE=keycloak` — the server has no caller token to forward or
exchange otherwise. The server raises `MissingAuthVerifierError` at startup if
you select `passthrough`/`exchange` while `MCP_AUTH_MODE=none`.

## The shared `IDP_*` anchor

`IDP_ISSUER` declares your identity provider's realm once. `IDP_TOKEN_URL` is
derived from it by Keycloak convention (`<issuer>/protocol/openid-connect/token`)
unless you override it explicitly. The JWKS endpoint is derived by FastMCP's
`KeycloakAuthProvider` directly from the issuer and is not separately
configurable. `IDP_AUDIENCE` is the default audience used by both boundaries.

Any of the per-boundary audience overrides (`MCP_AUTH_AUDIENCE`,
`TEMPORAL_OIDC_AUDIENCE`, `TEMPORAL_EXCHANGE_AUDIENCE`, ...) can override the
`IDP_AUDIENCE` anchor for that one task — for example, running incoming
verification against one audience while the outbound token targets another.

## Guides

1. [Keycloak setup](keycloak-setup.md) — realm, client, and audience mapper shared
   by every mode.
2. [Mode: service](mode-service.md) — one machine identity via client credentials.
3. [Mode: passthrough](mode-passthrough.md) — forward the caller's own token.
4. [Mode: exchange](mode-exchange.md) — RFC 8693 token exchange per request.
5. [Incoming auth / SSO](incoming-sso.md) — how callers authenticate to this
   server in the first place.
