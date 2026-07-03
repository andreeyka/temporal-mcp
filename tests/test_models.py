from temporal_mcp.models import (
    ActionResult,
    ActivityDetail,
    ActivitySummary,
    BatchOperationDetail,
    BatchOperationSummary,
    ClusterInfo,
    ExecutionDetail,
    ExecutionSummary,
    FailureInfo,
    HistoryEventModel,
    NamespaceDetail,
    NamespaceSummary,
    NexusEndpointDetail,
    NexusEndpointSummary,
    ScheduleDetail,
    ScheduleList,
    ScheduleSummary,
    SearchAttributesInfo,
    TaskQueueInfo,
    TaskQueuePoller,
    WorkerDeploymentDetail,
    WorkerDeploymentSummary,
    WorkflowRuleDetail,
    WorkflowRuleSummary,
)


def test_workflow_models_construct_and_dump():
    summ = _execution_summary()
    assert summ.model_dump()["status"] == "FAILED"
    det = ExecutionDetail(**summ.model_dump(), search_attributes={"k": "v"})
    assert det.search_attributes == {"k": "v"}
    fi = FailureInfo(message="boom", type="application", stack_trace=None)
    ev = HistoryEventModel(event_id=1, event_time=None, event_type="X", failure=fi, reason=None)
    assert ev.failure.message == "boom"


def test_namespace_models_construct_and_dump():
    assert NamespaceSummary(name="n", state="Registered", description="", retention_seconds=None).name == "n"
    assert NamespaceDetail(
        name="n", state="s", description="", retention_seconds=1, owner_email="e", is_global=True
    ).is_global
    assert ClusterInfo(server_version="1.0", capabilities={"a": True}).capabilities["a"]


def test_new_output_models_construct_and_dump():
    assert ActivitySummary(activity_id="a", activity_type="T").activity_id == "a"
    assert ActivityDetail(activity_id="a", attempt=2).attempt == 2
    assert BatchOperationSummary(job_id="j", state="RUNNING").job_id == "j"
    assert BatchOperationDetail(job_id="j", operation_type="TERMINATE").operation_type == "TERMINATE"
    assert NexusEndpointSummary(id="e", version=1, name="n").name == "n"
    assert NexusEndpointDetail(id="e", version=1, name="n", target={"kind": "worker"}).target["kind"] == "worker"
    assert ScheduleSummary(id="s", workflow_type="W").workflow_type == "W"
    assert ScheduleList(namespace="ns", count=1, schedules=[ScheduleSummary(id="s")]).count == 1
    assert ScheduleDetail(id="s", paused=True).paused is True
    assert TaskQueuePoller(identity="worker", last_access_time="now").identity == "worker"
    assert TaskQueueInfo(namespace="ns", task_queue="q", pollers=[]).task_queue == "q"
    assert SearchAttributesInfo(namespace="ns", custom={"Custom": "KEYWORD"}, system={}).custom["Custom"] == "KEYWORD"
    assert WorkerDeploymentSummary(name="d").name == "d"
    assert WorkerDeploymentDetail(name="d", version_count=3).version_count == 3
    assert WorkflowRuleSummary(id="r", visibility_query="WorkflowType='W'").id == "r"
    assert WorkflowRuleDetail(id="r", actions=["pause"]).actions == ["pause"]
    assert ActionResult(ok=True, workflow_id="wf").model_dump()["workflow_id"] == "wf"


def test_activity_and_batch_model_dump_shapes():
    activity = ActivitySummary(activity_id="a").model_dump(mode="json")
    batch = BatchOperationDetail(job_id="j", operation_type="TERMINATE").model_dump(mode="json")
    assert activity == _activity_json_shape()
    assert batch == _batch_json_shape()


def test_nexus_and_schedule_model_dump_shapes():
    nexus = NexusEndpointDetail(id="e", name="n", target={"kind": "worker"}).model_dump(mode="json")
    schedules = ScheduleList(namespace="ns", count=1, schedules=[ScheduleSummary(id="s")]).model_dump(mode="json")
    schedule = ScheduleDetail(id="s", next_action_times=["now"]).model_dump(mode="json")
    assert nexus["target"] == {"kind": "worker"}
    assert schedules["schedules"] == [_schedule_summary_json_shape()]
    assert schedule["next_action_times"] == ["now"]


def test_task_queue_model_dump_shapes():
    task_queue = TaskQueueInfo(
        namespace="ns",
        task_queue="q",
        pollers=[TaskQueuePoller(identity="worker")],
    ).model_dump(mode="json")
    search_attrs = SearchAttributesInfo(namespace="ns", custom={"Custom": "KEYWORD"}, system={}).model_dump(mode="json")
    assert task_queue["pollers"] == [_task_queue_poller_json_shape()]
    assert search_attrs == {"namespace": "ns", "custom": {"Custom": "KEYWORD"}, "system": {}}


def test_worker_deployment_and_rule_model_dump_shapes():
    deployment = WorkerDeploymentDetail(name="d", version_count=3).model_dump(mode="json")
    rule = WorkflowRuleDetail(id="r", actions=["pause"]).model_dump(mode="json")
    assert deployment["version_count"] == 3
    assert rule == _workflow_rule_json_shape()


def _activity_json_shape():
    return {
        "activity_id": "a",
        "activity_run_id": None,
        "activity_type": None,
        "status": None,
        "task_queue": None,
        "scheduled_time": None,
        "close_time": None,
    }


def _execution_summary():
    return ExecutionSummary(
        namespace="ns",
        workflow_id="wf",
        run_id="r",
        workflow_type="T",
        task_queue="tq",
        status="FAILED",
        start_time="2026-01-01T00:00:00+00:00",
        close_time=None,
        execution_time=None,
        history_length=42,
        parent_id=None,
        parent_run_id=None,
        root_id=None,
    )


def _batch_json_shape():
    return {
        "job_id": "j",
        "state": None,
        "start_time": None,
        "close_time": None,
        "operation_type": "TERMINATE",
        "total_operation_count": 0,
        "complete_operation_count": 0,
        "failure_operation_count": 0,
        "identity": "",
        "reason": "",
    }


def _schedule_summary_json_shape():
    return {"id": "s", "workflow_type": None}


def _task_queue_poller_json_shape():
    return {"identity": "worker", "last_access_time": None}


def _workflow_rule_json_shape():
    return {
        "id": "r",
        "visibility_query": "",
        "description": "",
        "created_by_identity": "",
        "create_time": None,
        "actions": ["pause"],
        "expiration_time": None,
    }
