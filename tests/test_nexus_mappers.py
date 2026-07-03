"""Tests for Nexus endpoint mappers."""

from datetime import UTC, datetime

from google.protobuf.timestamp_pb2 import Timestamp
from temporalio.api.nexus.v1 import Endpoint, EndpointSpec, EndpointTarget

from temporal_mcp.mappers import nexus_mapper as mapper
from temporal_mcp.models import NexusEndpointDetail, NexusEndpointSummary


def _ts(year: int = 2026) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(datetime(year, 1, 1, tzinfo=UTC))
    return ts


def _worker_endpoint() -> Endpoint:
    spec = EndpointSpec(
        name="my-endpoint",
        target=EndpointTarget(worker=EndpointTarget.Worker(namespace="target-ns", task_queue="tq")),
    )
    return Endpoint(
        id="ep-1",
        version=3,
        spec=spec,
        created_time=_ts(2025),
        last_modified_time=_ts(),
        url_prefix="/nexus/ep-1",
    )


def test_summary_shapes_fields():
    out = mapper.nexus_endpoint_summary(_worker_endpoint())
    assert isinstance(out, NexusEndpointSummary)
    assert out.model_dump(mode="json") == {
        "id": "ep-1",
        "version": 3,
        "name": "my-endpoint",
        "url_prefix": "/nexus/ep-1",
        "created_time": _ts(2025).ToDatetime().isoformat(),
    }


def test_summary_handles_missing_created_time():
    out = mapper.nexus_endpoint_summary(Endpoint(id="ep-2", version=1, spec=EndpointSpec(name="n")))
    assert out.created_time is None


def test_detail_includes_last_modified_and_worker_target():
    out = mapper.nexus_endpoint_detail(_worker_endpoint())
    assert isinstance(out, NexusEndpointDetail)
    assert out.id == "ep-1"
    assert out.last_modified_time == _ts().ToDatetime().isoformat()
    assert out.target == {"kind": "worker", "namespace": "target-ns", "task_queue": "tq"}


def test_detail_external_target():
    spec = EndpointSpec(name="ext", target=EndpointTarget(external=EndpointTarget.External(url="https://example.com")))
    out = mapper.nexus_endpoint_detail(Endpoint(id="ep-3", version=1, spec=spec))
    assert out.target == {"kind": "external", "url": "https://example.com"}


def test_detail_missing_last_modified_time():
    out = mapper.nexus_endpoint_detail(Endpoint(id="ep-4", version=1, spec=EndpointSpec(name="n")))
    assert out.last_modified_time is None


def test_nexus_endpoint_summaries_maps_each_endpoint():
    assert mapper.nexus_endpoint_summaries([_worker_endpoint()]) == [mapper.nexus_endpoint_summary(_worker_endpoint())]
