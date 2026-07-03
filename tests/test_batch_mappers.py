"""Tests for batch-operation mappers."""

from datetime import UTC, datetime

from google.protobuf.timestamp_pb2 import Timestamp
from temporalio.api.batch.v1 import BatchOperationInfo
from temporalio.api.enums.v1 import BatchOperationState, BatchOperationType
from temporalio.api.workflowservice.v1 import DescribeBatchOperationResponse

from temporal_mcp.mappers import batch_mapper as mapper
from temporal_mcp.models import BatchOperationDetail, BatchOperationSummary


def _ts():
    ts = Timestamp()
    ts.FromDatetime(datetime(2026, 1, 1, tzinfo=UTC))
    return ts


def _summary_info():
    return BatchOperationInfo(
        job_id="job-1",
        state=BatchOperationState.BATCH_OPERATION_STATE_RUNNING,
        start_time=_ts(),
        close_time=_ts(),
    )


def _detail_response():
    return DescribeBatchOperationResponse(
        job_id="job-1",
        operation_type=BatchOperationType.BATCH_OPERATION_TYPE_TERMINATE,
        state=BatchOperationState.BATCH_OPERATION_STATE_COMPLETED,
        start_time=_ts(),
        close_time=_ts(),
        total_operation_count=10,
        complete_operation_count=8,
        failure_operation_count=2,
        identity="me",
        reason="cleanup",
    )


def test_summary_shapes_fields():
    out = mapper.batch_operation_summary(_summary_info())
    assert isinstance(out, BatchOperationSummary)
    assert out.model_dump(mode="json") == {
        "job_id": "job-1",
        "state": "BATCH_OPERATION_STATE_RUNNING",
        "start_time": _ts().ToDatetime().isoformat(),
        "close_time": _ts().ToDatetime().isoformat(),
    }


def test_summary_handles_missing_timestamps():
    info = BatchOperationInfo(job_id="job-2", state=BatchOperationState.BATCH_OPERATION_STATE_COMPLETED)
    out = mapper.batch_operation_summary(info)
    assert out.start_time is None
    assert out.close_time is None


def test_detail_shapes_fields():
    out = mapper.batch_operation_detail(_detail_response())
    assert isinstance(out, BatchOperationDetail)
    assert out.model_dump(mode="json") == {
        "job_id": "job-1",
        "state": "BATCH_OPERATION_STATE_COMPLETED",
        "start_time": _ts().ToDatetime().isoformat(),
        "close_time": _ts().ToDatetime().isoformat(),
        "operation_type": "BATCH_OPERATION_TYPE_TERMINATE",
        "total_operation_count": 10,
        "complete_operation_count": 8,
        "failure_operation_count": 2,
        "identity": "me",
        "reason": "cleanup",
    }


def test_detail_handles_missing_timestamps():
    out = mapper.batch_operation_detail(DescribeBatchOperationResponse(job_id="job-2"))
    assert out.start_time is None
    assert out.close_time is None


def test_batch_operation_summaries_maps_each_operation():
    assert mapper.batch_operation_summaries([_summary_info()]) == [mapper.batch_operation_summary(_summary_info())]
