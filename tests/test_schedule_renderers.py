"""Tests for schedule renderers."""

from temporal_mcp.models import ScheduleDetail, ScheduleList, ScheduleSummary
from temporal_mcp.renderers import schedule_renderer


def test_schedule_list_renders_meta_and_items_section() -> None:
    payload = ScheduleList(
        namespace="default",
        count=1,
        schedules=[ScheduleSummary(id="schedule-1", workflow_type="WorkflowA")],
    )

    text = schedule_renderer.schedule_list(payload)

    assert "## Schedules" in text
    assert "## Items" in text
    assert "| id | workflow_type |" in text
    assert "schedule-1" in text


def test_schedule_list_renders_items_section_when_empty() -> None:
    payload = ScheduleList(namespace="default", count=0, schedules=[])

    text = schedule_renderer.schedule_list(payload)

    assert "## Schedules" in text
    assert "## Items" in text
    assert "_No items._" in text


def test_schedule_detail_renders_schedule_section() -> None:
    payload = ScheduleDetail(id="schedule-1", note="maintenance", paused=True)

    text = schedule_renderer.schedule_detail(payload)

    assert "## Schedule" in text
    assert "**id**" in text
    assert "schedule-1" in text
