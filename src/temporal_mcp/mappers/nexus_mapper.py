"""Mappers for Nexus endpoint protobuf objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import oneof_name, timestamp_field_to_iso
from temporal_mcp.models import NexusEndpointDetail, NexusEndpointSummary


# Any is constrained to protobuf mapper boundaries with dynamic attributes.


def _target(raw: object) -> dict[str, object] | None:
    endpoint = cast("Any", raw)
    variant = oneof_name(endpoint.spec.target, "variant")
    if variant == "worker":
        worker = endpoint.spec.target.worker
        return {"kind": "worker", "namespace": worker.namespace, "task_queue": worker.task_queue}
    if variant == "external":
        return {"kind": "external", "url": endpoint.spec.target.external.url}
    return None


def nexus_endpoint_summary(raw: object) -> NexusEndpointSummary:
    """Map a Nexus endpoint proto to a Nexus endpoint summary model."""
    endpoint = cast("Any", raw)
    return NexusEndpointSummary(
        id=endpoint.id,
        version=endpoint.version,
        name=endpoint.spec.name,
        url_prefix=endpoint.url_prefix,
        created_time=timestamp_field_to_iso(endpoint, "created_time"),
    )


def nexus_endpoint_detail(raw: object) -> NexusEndpointDetail:
    """Map a Nexus endpoint proto to a Nexus endpoint detail model."""
    endpoint = cast("Any", raw)
    summary = nexus_endpoint_summary(raw).model_dump()
    return NexusEndpointDetail(
        **summary,
        last_modified_time=timestamp_field_to_iso(endpoint, "last_modified_time"),
        target=_target(endpoint),
    )


def nexus_endpoint_summaries(raw: list[object]) -> list[NexusEndpointSummary]:
    """Map Nexus endpoint protos to Nexus endpoint summary models."""
    return [nexus_endpoint_summary(endpoint) for endpoint in raw]
