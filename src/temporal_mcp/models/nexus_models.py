"""Pydantic models for Nexus endpoint results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class NexusEndpointSummary(BaseModel):
    """Summary of a Nexus endpoint."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: Annotated[str, Field(description="Nexus endpoint ID.")]
    version: Annotated[int, Field(description="Nexus endpoint version.")] = 0
    name: Annotated[str, Field(description="Nexus endpoint name.")]
    url_prefix: Annotated[str, Field(description="Nexus endpoint URL prefix.")] = ""
    created_time: Annotated[str | None, Field(description="ISO-8601 created time.")] = None


class NexusEndpointDetail(NexusEndpointSummary):
    """Detailed Nexus endpoint state."""

    last_modified_time: Annotated[str | None, Field(description="ISO-8601 last modified time.")] = None
    target: Annotated[dict[str, object] | None, Field(description="Nexus endpoint target details.")] = None
