"""Render workflow output models and payloads as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from temporal_mcp.renderers import markdown as md
from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import ClusterInfo, ExecutionDetail, ExecutionSummary


_ENTITY_RENDERER = EntityRenderer()
_EXEC_COLUMNS = (
    "namespace",
    "workflow_id",
    "run_id",
    "workflow_type",
    "task_queue",
    "status",
    "start_time",
    "close_time",
    "execution_time",
    "history_length",
    "parent_id",
    "parent_run_id",
    "root_id",
)
_EVENT_COLUMNS = ("event_id", "event_time", "event_type", "reason", "activity_type", "activity_id")
_FAILURE_COLUMNS = ("event_id", "type", "message", "stack_trace")
_GROUP_COLUMNS = ("count", "values")
_EXEC_SPEC = RenderSpec(title="Workflows", columns=_EXEC_COLUMNS)


def execution_list(items: list[ExecutionSummary]) -> str:
    """Render workflow execution summaries as Markdown."""
    return _ENTITY_RENDERER.list(items, _EXEC_SPEC)


def execution_detail(detail: ExecutionDetail) -> str:
    """Render one workflow execution as Markdown."""
    body = detail.model_dump(mode="json")
    search = body.pop("search_attributes", {})
    text = md.dict_block(body, "Workflow")
    if search:
        text = md.sections([text, md.heading("Search Attributes", 3), md.kv(search)])
    return text


def history(payload: dict[str, object]) -> str:
    """Render workflow history payload as Markdown."""
    meta = {key: payload[key] for key in ("namespace", "workflow_id", "run_id") if key in payload}
    raw_events = payload.get("events", [])
    parts = [md.dict_block(meta, "Workflow History")]
    events: list[dict[str, Any]] = []
    if isinstance(raw_events, list):
        events = cast("list[dict[str, Any]]", [event for event in raw_events if isinstance(event, dict)])
    parts.append(md.dict_table(events, "Events", columns=_EVENT_COLUMNS))
    failures = _failure_rows(events)
    if failures:
        parts.append(md.dict_table(failures, "Failures", columns=_FAILURE_COLUMNS))
    return md.sections(parts)


def count(payload: dict[str, object]) -> str:
    """Render workflow count payload as Markdown."""
    summary = {key: payload[key] for key in ("namespace", "query", "count") if key in payload}
    raw_groups = payload.get("groups", [])
    parts = [md.dict_block(summary, "Workflow Count")]
    groups: list[dict[str, Any]] = []
    if isinstance(raw_groups, list):
        groups = cast("list[dict[str, Any]]", [group for group in raw_groups if isinstance(group, dict)])
    parts.append(md.dict_table(groups, "Groups", columns=_GROUP_COLUMNS))
    return md.sections(parts)


def cluster_info(info: ClusterInfo) -> str:
    """Render cluster info as Markdown."""
    body = info.model_dump(mode="json")
    caps = body.pop("capabilities", {})
    text = md.dict_block(body, "Cluster Info")
    if caps:
        text = md.sections([text, md.heading("Capabilities", 3), md.kv(caps)])
    return text


def _failure_rows(events: list[dict[str, Any]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in events:
        failure = event.get("failure")
        if isinstance(failure, dict):
            rows.append({"event_id": event.get("event_id"), **failure})
    return rows
