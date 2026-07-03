"""Mappers for worker deployment protobuf objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import timestamp_field_to_iso
from temporal_mcp.models import WorkerDeploymentDetail, WorkerDeploymentSummary


# Any is constrained to protobuf mapper boundaries with dynamic attributes.


def worker_deployment_summary(raw: object) -> WorkerDeploymentSummary:
    """Map a worker deployment proto to a worker deployment summary model."""
    summary = cast("Any", raw)
    return WorkerDeploymentSummary(
        name=summary.name,
        create_time=timestamp_field_to_iso(summary, "create_time"),
    )


def worker_deployment_detail(raw: object) -> WorkerDeploymentDetail:
    """Map a worker deployment info proto to a worker deployment detail model."""
    info = cast("Any", raw)
    return WorkerDeploymentDetail(
        name=info.name,
        create_time=timestamp_field_to_iso(info, "create_time"),
        last_modifier_identity=info.last_modifier_identity,
        manager_identity=info.manager_identity,
        version_count=len(info.version_summaries),
    )


def worker_deployment_summaries(raw: list[object]) -> list[WorkerDeploymentSummary]:
    """Map worker deployment protos to worker deployment summary models."""
    return [worker_deployment_summary(summary) for summary in raw]
