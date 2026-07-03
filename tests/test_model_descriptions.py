"""Every entity-model field must carry a non-empty Field(description=...)."""

import pytest

from temporal_mcp.models import (
    action_models,
    activity_models,
    batch_models,
    failure_models,
    namespace_models,
    nexus_models,
    schedule_models,
    task_queue_models,
    worker_deployment_models,
    workflow_models,
    workflow_rule_models,
)


MODELS = [
    action_models.ActionResult,
    activity_models.ActivitySummary,
    activity_models.ActivityDetail,
    batch_models.BatchOperationSummary,
    batch_models.BatchOperationDetail,
    failure_models.RootCause,
    failure_models.CauseLink,
    failure_models.LastFailedActivity,
    failure_models.WorkflowFailureAnalysis,
    failure_models.FailureGroup,
    failure_models.FailureSummary,
    namespace_models.NamespaceSummary,
    namespace_models.NamespaceDetail,
    namespace_models.ClusterInfo,
    nexus_models.NexusEndpointSummary,
    nexus_models.NexusEndpointDetail,
    schedule_models.ScheduleSummary,
    schedule_models.ScheduleList,
    schedule_models.ScheduleDetail,
    task_queue_models.TaskQueuePoller,
    task_queue_models.TaskQueueInfo,
    task_queue_models.SearchAttributesInfo,
    worker_deployment_models.WorkerDeploymentSummary,
    worker_deployment_models.WorkerDeploymentDetail,
    workflow_models.FailureInfo,
    workflow_models.ExecutionSummary,
    workflow_models.ExecutionDetail,
    workflow_models.HistoryEventModel,
    workflow_rule_models.WorkflowRuleSummary,
    workflow_rule_models.WorkflowRuleDetail,
]


@pytest.mark.parametrize("model", MODELS, ids=[m.__name__ for m in MODELS])
def test_every_field_has_description(model):
    missing = [name for name, f in model.model_fields.items() if not (f.description or "").strip()]
    assert not missing, f"{model.__name__} fields missing description: {missing}"
