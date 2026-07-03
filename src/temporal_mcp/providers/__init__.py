"""Dependency providers."""

from temporal_mcp.providers.client_provider import (
    TemporalClientPoolProvider,
    get_client_pool,
)
from temporal_mcp.providers.service_provider import (
    TemporalActivityServiceProvider,
    TemporalBatchServiceProvider,
    TemporalFailureServiceProvider,
    TemporalNamespaceServiceProvider,
    TemporalNexusServiceProvider,
    TemporalScheduleServiceProvider,
    TemporalTaskQueueServiceProvider,
    TemporalWorkerDeploymentServiceProvider,
    TemporalWorkflowRuleServiceProvider,
    TemporalWorkflowServiceProvider,
)


__all__ = [
    "TemporalActivityServiceProvider",
    "TemporalBatchServiceProvider",
    "TemporalClientPoolProvider",
    "TemporalFailureServiceProvider",
    "TemporalNamespaceServiceProvider",
    "TemporalNexusServiceProvider",
    "TemporalScheduleServiceProvider",
    "TemporalTaskQueueServiceProvider",
    "TemporalWorkerDeploymentServiceProvider",
    "TemporalWorkflowRuleServiceProvider",
    "TemporalWorkflowServiceProvider",
    "get_client_pool",
]
