"""Tests for schedule mappers."""

from datetime import UTC, datetime
from types import SimpleNamespace

from temporal_mcp.mappers import schedule_mapper
from temporal_mcp.models import ScheduleDetail, ScheduleList, ScheduleSummary


def _summary(schedule_id: str = "schedule-1", workflow_type: str = "WorkflowA") -> SimpleNamespace:
    return SimpleNamespace(id=schedule_id, info=SimpleNamespace(workflow_type=workflow_type))


def _description() -> SimpleNamespace:
    return SimpleNamespace(
        schedule=SimpleNamespace(state=SimpleNamespace(note="maintenance", paused=True)),
        info=SimpleNamespace(next_action_times=[datetime(2026, 1, 2, 3, 4, tzinfo=UTC)]),
    )


def test_schedule_summary_maps_fields() -> None:
    result = schedule_mapper.schedule_summary(_summary())

    assert isinstance(result, ScheduleSummary)
    assert result.model_dump(mode="json") == {
        "id": "schedule-1",
        "workflow_type": "WorkflowA",
    }


def test_schedule_list_maps_namespace_count_and_items() -> None:
    result = schedule_mapper.schedule_list("default", [_summary(), _summary("schedule-2", "WorkflowB")])

    assert isinstance(result, ScheduleList)
    assert result.model_dump(mode="json") == {
        "namespace": "default",
        "count": 2,
        "schedules": [
            {"id": "schedule-1", "workflow_type": "WorkflowA"},
            {"id": "schedule-2", "workflow_type": "WorkflowB"},
        ],
    }


def test_schedule_detail_maps_state_and_next_action_times() -> None:
    result = schedule_mapper.schedule_detail("schedule-1", _description())

    assert isinstance(result, ScheduleDetail)
    assert result.model_dump(mode="json") == {
        "id": "schedule-1",
        "note": "maintenance",
        "paused": True,
        "next_action_times": ["2026-01-02T03:04:00+00:00"],
    }


def test_schedule_detail_handles_missing_next_action_times() -> None:
    raw = SimpleNamespace(
        schedule=SimpleNamespace(state=SimpleNamespace(note="", paused=False)),
        info=SimpleNamespace(next_action_times=None),
    )

    result = schedule_mapper.schedule_detail("schedule-2", raw)

    assert result.next_action_times == []


def test_schedule_detail_treats_none_note_as_empty_string() -> None:
    raw = SimpleNamespace(
        schedule=SimpleNamespace(state=SimpleNamespace(note=None, paused=False)),
        info=SimpleNamespace(next_action_times=[]),
    )

    result = schedule_mapper.schedule_detail("schedule-3", raw)

    assert result.note == ""
