# Release Notes

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
