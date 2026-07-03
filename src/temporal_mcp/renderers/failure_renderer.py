"""Markdown renderers for failure-analysis models."""

from __future__ import annotations

from temporal_mcp.models import FailureGroup, FailureSummary, RootCause, WorkflowFailureAnalysis
from temporal_mcp.renderers import markdown as md


def failure_analysis(analysis: WorkflowFailureAnalysis) -> str:
    """Render workflow failure analysis as Markdown."""
    body = analysis.model_dump()
    root = body.pop("root_cause", None)
    chain = body.pop("cause_chain", [])
    activity = body.pop("last_failed_activity", None)
    parts = [md.dict_block(body, "Workflow Failure Analysis")]
    if root:
        parts.append(_root_cause(RootCause.model_validate(root)))
    if chain:
        parts.append(md.dict_table(chain, "Cause Chain", columns=("category", "error_type", "message")))
    if activity:
        parts.append(md.dict_block(activity, "Last Failed Activity"))
    return md.sections(parts)


def failure_summary(summary: FailureSummary) -> str:
    """Render namespace failure summary as Markdown."""
    body = summary.model_dump()
    by_type = body.pop("by_workflow_type", [])
    by_error = body.pop("by_error_type", [])
    note = body.pop("note", "")
    parts = [
        md.dict_block(body, "Failure Summary"),
        md.dict_table(by_type, "By Workflow Type", columns=("key", "count")),
        md.dict_table(by_error, "By Error Type", columns=("key", "count", "sampled")),
    ]
    if note:
        parts.append(f"_{note}_")
    return md.sections(parts)


def failure_groups(groups: list[FailureGroup], title: str = "Top Failure Types") -> str:
    """Render ranked failure groups as Markdown."""
    rows = [group.model_dump() for group in groups]
    return md.dict_table(rows, title, columns=("key", "count", "sampled"))


def _root_cause(cause: RootCause) -> str:
    """Render a root cause as Markdown."""
    return md.dict_block(cause.model_dump(), "Root Cause")
