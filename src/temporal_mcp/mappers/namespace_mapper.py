"""Mappers for namespace SDK responses."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.models import NamespaceDetail, NamespaceSummary


def _retention(config: Any) -> int | None:  # noqa: ANN401
    """Return retention TTL in seconds, or None."""
    if config.HasField("workflow_execution_retention_ttl"):
        return int(config.workflow_execution_retention_ttl.ToSeconds())
    return None


def namespace_summary(raw: object) -> NamespaceSummary:
    """Build a NamespaceSummary from a ListNamespaces entry."""
    namespace = cast("Any", raw)
    return NamespaceSummary(
        name=namespace.namespace_info.name,
        state=str(namespace.namespace_info.state),
        description=namespace.namespace_info.description,
        retention_seconds=_retention(namespace.config),
    )


def namespace_detail(raw: object) -> NamespaceDetail:
    """Build a NamespaceDetail from a DescribeNamespace response."""
    response = cast("Any", raw)
    info = response.namespace_info
    return NamespaceDetail(
        name=info.name,
        state=str(info.state),
        description=info.description,
        owner_email=info.owner_email,
        retention_seconds=_retention(response.config),
        is_global=response.is_global_namespace,
    )
