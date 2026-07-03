"""Mappers for batch operation protobuf objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import proto_enum_name, timestamp_field_to_iso
from temporal_mcp.models import BatchOperationDetail, BatchOperationSummary


# Any is constrained to protobuf mapper boundaries with dynamic attributes.


def batch_operation_summary(raw: object) -> BatchOperationSummary:
    """Map a batch operation proto to a batch operation summary model."""
    info = cast("Any", raw)
    return BatchOperationSummary(
        job_id=info.job_id,
        state=proto_enum_name(info, "state"),
        start_time=timestamp_field_to_iso(info, "start_time"),
        close_time=timestamp_field_to_iso(info, "close_time"),
    )


def batch_operation_detail(raw: object) -> BatchOperationDetail:
    """Map a batch operation description proto to a detail model."""
    resp = cast("Any", raw)
    return BatchOperationDetail(
        job_id=resp.job_id,
        operation_type=proto_enum_name(resp, "operation_type"),
        state=proto_enum_name(resp, "state"),
        start_time=timestamp_field_to_iso(resp, "start_time"),
        close_time=timestamp_field_to_iso(resp, "close_time"),
        total_operation_count=resp.total_operation_count,
        complete_operation_count=resp.complete_operation_count,
        failure_operation_count=resp.failure_operation_count,
        identity=resp.identity,
        reason=resp.reason,
    )


def batch_operation_summaries(raw: list[object]) -> list[BatchOperationSummary]:
    """Map batch operation protos to batch operation summary models."""
    return [batch_operation_summary(info) for info in raw]
