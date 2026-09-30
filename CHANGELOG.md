# Release Notes

## 0.1.3 - 2026-09-30

### Added

- Tool-call audit records with caller identity, tool name, outcome, and duration, including cancelled calls. Arguments, results, tokens, and exception messages are omitted.
- Optional trusted proxy username header and environment settings for audit logging, MCP endpoint path, and server log level.
- An unauthenticated `/health` endpoint for HTTP process probes.
- Docker Compose configuration and configurable Python/uv build images and target platforms.
- Manual release rebuilds with package-version validation and matching release metadata.

### Changed

- Run the container with numeric UID/GID `10001:10001` and document read-only filesystem support and Kubernetes deployment settings.
- Make the example environment compatible with Docker env files and leave example SSO settings disabled by default.
- Update deployment examples to use the `v0.1.3` image.

## 0.1.2 - 2026-07-04

### Added

- Added an optional `include_payloads` parameter to the `get_workflow_history` tool. When enabled, it surfaces decoded workflow/activity `input` and `result` payloads (UTF-8), each truncated with a marker, in a dedicated `Payloads` section and in structured output. Disabled by default; payloads may expose sensitive data.

## 0.1.1 - 2026-07-03

### Added

- Added optional `MCP_AUTH_CLAIM_EXPR` for incoming Keycloak auth. The value is a CEL expression evaluated against verified JWT claims, including Keycloak `groups` allowlists.
- Added `cel-python` as the CEL runtime for incoming claim authorization.
- Added FastMCP middleware enforcement for claim expressions, so valid JWTs that fail CEL are rejected as authorization failures instead of invalid tokens.

### Changed

- Kept `aud` validation as a system-level JWT check through `MCP_AUTH_AUDIENCE` or `IDP_AUDIENCE`; claim expressions run only after signature, issuer, and audience validation succeed.
