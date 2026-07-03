"""Pydantic models for namespace and cluster results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class NamespaceSummary(BaseModel):
    """Summary of a namespace."""

    model_config = ConfigDict(extra="ignore")

    name: Annotated[str, Field(description="Namespace name.")]
    state: Annotated[str, Field(description="Namespace state (e.g. Registered, Deprecated, Deleted).")]
    description: Annotated[str, Field(description="Namespace description.")] = ""
    retention_seconds: Annotated[int | None, Field(description="Workflow execution retention period in seconds.")] = (
        None
    )


class NamespaceDetail(NamespaceSummary):
    """Namespace summary plus ownership and scope."""

    owner_email: Annotated[str, Field(description="Owner email for the namespace.")] = ""
    is_global: Annotated[bool, Field(description="Whether the namespace is global (multi-cluster).")] = False


class ClusterInfo(BaseModel):
    """Cluster server version and capabilities."""

    model_config = ConfigDict(extra="ignore")

    server_version: Annotated[str, Field(description="Temporal server version.")]
    capabilities: Annotated[dict[str, bool], Field(description="Map of server capability flags.")] = Field(
        default_factory=dict
    )
