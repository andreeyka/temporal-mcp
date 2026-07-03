# Keycloak setup

Shared setup used by every outbound mode ([service](mode-service.md),
[passthrough](mode-passthrough.md), [exchange](mode-exchange.md)) and by
[incoming SSO](incoming-sso.md). All values below are fictional placeholders —
substitute your own realm, hostnames, and client IDs.

This guide assumes Keycloak, but any OIDC-compliant identity provider that
exposes a discovery document and JWKS works the same way.

## 1. Create the realm

In the Keycloak admin console: **Create realm** → name it `demo` (placeholder —
use your own realm name).

## 2. Find the endpoints

Realm settings → **Endpoints** → "OpenID Endpoint Configuration" opens the
realm's discovery document. From it, note:

- `issuer` → this is `IDP_ISSUER` (e.g. `https://sso.example.com/realms/demo`).
- `jwks_uri` → derived automatically as `<issuer>/protocol/openid-connect/certs`
  by FastMCP's `KeycloakAuthProvider`; not separately configurable.
- `token_endpoint` → derived automatically as `<issuer>/protocol/openid-connect/token`;
  only set `IDP_TOKEN_URL` to override.

Because the server derives JWKS and token URLs from `IDP_ISSUER`, in the common
case you only need to set the issuer.

## 3. Create a confidential client

Clients → **Create client**:

- Client ID: `temporal-mcp-svc` (placeholder — pick your own).
- **Client authentication: On** (this makes it a confidential client with a
  secret, required for client-credentials and token-exchange grants).

## 4. Enable a service account

On the client's **Settings** tab, turn **Service accounts roles: On**. This
lets the client mint its own client-credentials tokens (used by
[service mode](mode-service.md)) without a human login. Copy the client secret
from the **Credentials** tab — this becomes `TEMPORAL_OIDC_CLIENT_SECRET` (or
`TEMPORAL_EXCHANGE_CLIENT_SECRET` for a token-exchange client).

## 5. Add an Audience protocol mapper

Temporal only accepts tokens whose `aud` claim matches what its frontend is
configured to expect. Add a mapper so issued tokens carry the right audience:

Client scopes → open the client's dedicated scope (`<client-id>-dedicated`) →
**Add mapper** → **By configuration** → **Audience** →

- Included Custom Audience: `temporal-api` (placeholder — must match
  `IDP_AUDIENCE` / the mode-specific audience override).
- Add to access token: On.

## 6. (Optional) scope mapper

If you want to gate which clients can request a Temporal-scoped token, add a
client scope named `temporal` and a matching **scope** mapper, then require
that scope on the token request (`TEMPORAL_OIDC_SCOPE=temporal` /
`TEMPORAL_EXCHANGE_SCOPE=temporal`).

## Temporal-side trust

None of the above is useful unless the Temporal frontend is configured to trust
the same issuer and JWKS and to accept the `aud` you configured. See the
[Temporal server security / authorization documentation](https://docs.temporal.io/self-hosted-guide/security)
for how to configure your Temporal frontend's JWT authorizer. This repository
only controls what the MCP server sends — it does not configure Temporal itself.
