"""English error message templates."""

MSG_UNKNOWN_STATUS = "Unknown workflow status {status!r}. Valid values: {valid}"
MSG_AUTH_NO_TOKEN = (
    "Passthrough auth requires a caller bearer token, but none is present in the "  # noqa: S105
    "request context (is Authorization forwarded?)"
)
MSG_AUTH_UNKNOWN_MODE = "Unknown auth mode: {mode!r}"
MSG_AUTH_NO_SUBJECT = (
    "Passthrough/exchange auth requires a stable caller subject "
    "(subject, sub claim, or client_id), but none could be derived from the request token"
)
MSG_AUTH_VERIFIER_REQUIRED = (
    "TEMPORAL_AUTH_MODE={mode} requires incoming token verification: set "
    "MCP_AUTH_MODE=keycloak (with IDP_ISSUER and MCP_AUTH_BASE_URL) so caller tokens are validated"
)
MSG_INCOMING_AUTH_CONFIG = "MCP_AUTH_MODE={mode} requires {missing} to be set"
MSG_INCOMING_AUTH_POLICY_CONFIG = "MCP_AUTH_CLAIM_EXPR is invalid: {detail}"
MSG_INCOMING_AUTH_POLICY_DENIED = "Bearer token does not satisfy MCP_AUTH_CLAIM_EXPR"
MSG_CONNECTION = "Failed to connect to Temporal frontend {host}"
MSG_CONNECTION_WITH_DETAIL = "Failed to connect to Temporal frontend {host}: {detail}"
MSG_EXCHANGE = "Token exchange failed"
MSG_EXCHANGE_WITH_DETAIL = "Token exchange failed: {detail}"
MSG_SCHEDULE_SPEC_REQUIRED = "A schedule requires either a cron expression or an interval (in seconds)"
MSG_AUTH_WRONG_TOKEN_TYPE = (
    "Caller token has typ={typ!r}; only access tokens (typ='Bearer') may be forwarded to Temporal"  # noqa: S105
)
MSG_RPC_UNSUPPORTED = "The connected Temporal server does not support this operation ({detail}). {hint}"
MSG_HINT_STANDALONE_ACTIVITIES = (
    "This API is part of standalone activities and requires Temporal Server >= 1.31.0 "
    "(dev server: Temporal CLI >= 1.7.0)."
)
MSG_HINT_UPGRADE = "Upgrading the Temporal server to a newer version may be required."
MSG_RPC_NOT_FOUND = "Temporal resource not found: {detail}"
MSG_RPC_ALREADY_EXISTS = "Temporal resource already exists: {detail}"
MSG_RPC_INVALID = "Temporal rejected the request ({status}): {detail}"
MSG_RPC_PERMISSION = "Temporal denied access ({status}): {detail}"
MSG_RPC_RATE_LIMITED = "Temporal rate limit or quota exceeded: {detail}. Retry later."
MSG_RPC_UNAVAILABLE = "Temporal server is unavailable ({status}): {detail}. Check TEMPORAL_HOST and server health."
