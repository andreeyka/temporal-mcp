"""Reusable prompts for Temporal triage and diagnostics."""

from __future__ import annotations

from typing import Annotated

from fastmcp.server.providers import LocalProvider
from pydantic import Field

from temporal_mcp.enums import TemporalToolTags


prompts_mcp = LocalProvider()

FAILURE_TAGS: set[str] = {TemporalToolTags.TEMPORAL, TemporalToolTags.NAMESPACE, TemporalToolTags.FAILURE}


@prompts_mcp.prompt(tags=FAILURE_TAGS)
def triage_namespace_failures(
    namespace: Annotated[str, Field(description="Namespace to triage")],
) -> str:
    """Build a prompt that triages failed workflows in a namespace.

    Args:
        namespace: Namespace to triage.

    Returns:
        A user-message prompt string.
    """
    return (
        f"Investigate failed workflows in the Temporal namespace '{namespace}'. "
        f"Use count_workflows with query 'ExecutionStatus=\"Failed\"' to find hotspots, "
        f'list_workflows(status="FAILED") to enumerate them, and get_workflow_history '
        f"to surface root-cause messages, types, and stack traces. Summarize the top "
        f"failure categories and likely causes."
    )


@prompts_mcp.prompt(tags={TemporalToolTags.TEMPORAL, TemporalToolTags.WORKFLOW, TemporalToolTags.FAILURE})
def diagnose_workflow_failure(
    namespace: Annotated[str, Field(description="Namespace of the workflow")],
    workflow_id: Annotated[str, Field(description="ID of the workflow to diagnose")],
) -> str:
    """Build a prompt that diagnoses the failure of a single workflow.

    Args:
        namespace: Namespace of the workflow.
        workflow_id: ID of the workflow to diagnose.

    Returns:
        A user-message prompt string.
    """
    return (
        f"Diagnose the failure of workflow '{workflow_id}' in the Temporal namespace "
        f"'{namespace}'. Call the analyze_workflow_failure tool (or read the resource "
        f"temporal://namespace/{namespace}/failures) to obtain the cause chain, then "
        f"explain the root cause, the failing activity if any, and concrete remediation steps."
    )


@prompts_mcp.prompt(tags={TemporalToolTags.TEMPORAL, TemporalToolTags.CLUSTER})
def cluster_health_review() -> str:
    """Build a prompt that reviews overall Temporal cluster health.

    Returns:
        A user-message prompt string.
    """
    return (
        "Review the health of the Temporal cluster. Call get_cluster_info for the server "
        "version and capabilities, enumerate namespaces with list_namespaces (or read the "
        "resource temporal://namespaces), then run summarize_namespace_failures per namespace "
        "to gauge failure load. Summarize the top risks and any namespaces needing attention."
    )
