"""Pydantic models for workflow rule results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class WorkflowRuleSummary(BaseModel):
    """Summary of a workflow rule."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: Annotated[str, Field(description="Workflow rule ID.")]
    visibility_query: Annotated[str, Field(description="Workflow rule visibility query.")] = ""
    description: Annotated[str, Field(description="Workflow rule description.")] = ""
    created_by_identity: Annotated[str, Field(description="Identity that created the workflow rule.")] = ""
    create_time: Annotated[str | None, Field(description="ISO-8601 create time.")] = None


class WorkflowRuleDetail(WorkflowRuleSummary):
    """Detailed workflow rule state."""

    actions: Annotated[list[str | None], Field(description="Workflow rule actions.")]
    expiration_time: Annotated[str | None, Field(description="ISO-8601 expiration time.")] = None
