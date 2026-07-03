"""Enumerations for the Temporal MCP server."""

from enum import StrEnum


class TransportType(StrEnum):
    """MCP transport type."""

    HTTP = "http"
    STREAMABLE_HTTP = "streamable-http"
    SSE = "sse"


class AuthMode(StrEnum):
    """How the server presents identity to the Temporal frontend."""

    SERVICE = "service"
    PASSTHROUGH = "passthrough"
    EXCHANGE = "exchange"


class IncomingAuthMode(StrEnum):
    """How MCP clients authenticate to this server (incoming boundary)."""

    NONE = "none"
    KEYCLOAK = "keycloak"


class TemporalToolTags(StrEnum):
    """Tags for Temporal tools (used for client-side filtering)."""

    TEMPORAL = "temporal"
    CLUSTER = "cluster"
    NAMESPACE = "namespace"
    WORKFLOW = "workflow"
    SCHEDULE = "schedule"
    TASK_QUEUE = "task_queue"
    ACTIVITY = "activity"
    WORKER_DEPLOYMENT = "worker_deployment"
    BATCH = "batch"
    FAILURE = "failure"
    SEARCH_ATTRIBUTE = "search_attribute"
    WORKFLOW_RULE = "workflow_rule"
    NEXUS = "nexus"
    READ = "read"
    MUTATING = "mutating"
