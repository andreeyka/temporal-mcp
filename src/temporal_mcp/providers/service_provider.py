"""Service dependency providers (bound to the pool singleton)."""

from __future__ import annotations

from fastmcp.dependencies import Depends

from temporal_mcp.providers.client_provider import get_client_pool
from temporal_mcp.services.activity_service import TemporalActivityService
from temporal_mcp.services.batch_service import TemporalBatchService
from temporal_mcp.services.failure_service import TemporalFailureService
from temporal_mcp.services.namespace_service import TemporalNamespaceService
from temporal_mcp.services.nexus_service import TemporalNexusService
from temporal_mcp.services.schedule_service import TemporalScheduleService
from temporal_mcp.services.task_queue_service import TemporalTaskQueueService
from temporal_mcp.services.worker_deployment_service import TemporalWorkerDeploymentService
from temporal_mcp.services.workflow_rule_service import TemporalWorkflowRuleService
from temporal_mcp.services.workflow_service import TemporalWorkflowService


def get_workflow_service() -> TemporalWorkflowService:
    """Return a workflow service bound to the pool singleton."""
    return TemporalWorkflowService(get_client_pool())


def get_namespace_service() -> TemporalNamespaceService:
    """Return a namespace service bound to the pool singleton."""
    return TemporalNamespaceService(get_client_pool())


def get_schedule_service() -> TemporalScheduleService:
    """Return a schedule service bound to the pool singleton."""
    return TemporalScheduleService(get_client_pool())


def get_task_queue_service() -> TemporalTaskQueueService:
    """Return a task-queue service bound to the pool singleton."""
    return TemporalTaskQueueService(get_client_pool())


def get_failure_service() -> TemporalFailureService:
    """Return a failure service bound to the pool singleton."""
    return TemporalFailureService(get_client_pool())


def get_activity_service() -> TemporalActivityService:
    """Return an activity service bound to the pool singleton."""
    return TemporalActivityService(get_client_pool())


def get_worker_deployment_service() -> TemporalWorkerDeploymentService:
    """Return a worker-deployment service bound to the pool singleton."""
    return TemporalWorkerDeploymentService(get_client_pool())


def get_batch_service() -> TemporalBatchService:
    """Return a batch service bound to the pool singleton."""
    return TemporalBatchService(get_client_pool())


def get_workflow_rule_service() -> TemporalWorkflowRuleService:
    """Return a workflow-rule service bound to the pool singleton."""
    return TemporalWorkflowRuleService(get_client_pool())


def get_nexus_service() -> TemporalNexusService:
    """Return a Nexus endpoint service bound to the pool singleton."""
    return TemporalNexusService(get_client_pool())


TemporalWorkflowServiceProvider = Depends(get_workflow_service)
TemporalNamespaceServiceProvider = Depends(get_namespace_service)
TemporalScheduleServiceProvider = Depends(get_schedule_service)
TemporalTaskQueueServiceProvider = Depends(get_task_queue_service)
TemporalFailureServiceProvider = Depends(get_failure_service)
TemporalActivityServiceProvider = Depends(get_activity_service)
TemporalWorkerDeploymentServiceProvider = Depends(get_worker_deployment_service)
TemporalBatchServiceProvider = Depends(get_batch_service)
TemporalWorkflowRuleServiceProvider = Depends(get_workflow_rule_service)
TemporalNexusServiceProvider = Depends(get_nexus_service)
