"""Helpers for building Temporal visibility queries."""

from __future__ import annotations

from temporalio.client import WorkflowExecutionStatus

from temporal_mcp.errors import UnknownWorkflowStatusError


_SPECIAL_CASE = {"CONTINUED_AS_NEW": "ContinuedAsNew", "TIMED_OUT": "TimedOut"}


def status_to_query(status: str | None) -> str | None:
    """Map a friendly status name to a visibility-query fragment.

    Args:
        status: Status name such as ``FAILED`` or ``running`` (case-insensitive).

    Returns:
        A fragment like ``ExecutionStatus="Failed"``, or None when status is None.

    Raises:
        UnknownWorkflowStatusError: If the status is not a valid execution status.
    """
    if not status:
        return None
    name = status.strip().upper()
    valid = {s.name for s in WorkflowExecutionStatus}
    if name not in valid:
        raise UnknownWorkflowStatusError(status, sorted(valid))
    pretty = _SPECIAL_CASE.get(name, name.capitalize())
    return f'ExecutionStatus="{pretty}"'
