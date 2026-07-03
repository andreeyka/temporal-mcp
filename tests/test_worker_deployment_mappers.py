"""Tests for worker-deployment mappers."""

from datetime import UTC, datetime

from google.protobuf.timestamp_pb2 import Timestamp
from temporalio.api.deployment.v1 import WorkerDeploymentInfo
from temporalio.api.workflowservice.v1 import ListWorkerDeploymentsResponse

from temporal_mcp.mappers import worker_deployment_mapper as mapper
from temporal_mcp.models import WorkerDeploymentDetail, WorkerDeploymentSummary


def _ts():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 1, 1, tzinfo=UTC))
    return ts


def _summary():
    return ListWorkerDeploymentsResponse.WorkerDeploymentSummary(name="d1", create_time=_ts())


def test_summary_shapes_name_and_time():
    out = mapper.worker_deployment_summary(_summary())
    assert isinstance(out, WorkerDeploymentSummary)
    assert out.model_dump(mode="json") == {
        "name": "d1",
        "create_time": _ts().ToDatetime().isoformat(),
    }


def test_summary_handles_missing_time():
    summary = ListWorkerDeploymentsResponse.WorkerDeploymentSummary(name="d2")
    assert mapper.worker_deployment_summary(summary).create_time is None


def test_detail_shapes_fields():
    info = WorkerDeploymentInfo(name="d1", create_time=_ts(), last_modifier_identity="alice", manager_identity="mgr")
    out = mapper.worker_deployment_detail(info)
    assert isinstance(out, WorkerDeploymentDetail)
    assert out.name == "d1"
    assert out.last_modifier_identity == "alice"
    assert out.manager_identity == "mgr"
    assert out.version_count == 0
    assert out.create_time == _ts().ToDatetime().isoformat()


def test_worker_deployment_summaries_maps_each_deployment():
    assert mapper.worker_deployment_summaries([_summary()]) == [mapper.worker_deployment_summary(_summary())]
