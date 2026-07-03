"""Tests for task queue renderers."""

from temporal_mcp.models import SearchAttributesInfo, TaskQueueInfo, TaskQueuePoller
from temporal_mcp.renderers import task_queue_renderer


def test_task_queue_renders_meta_and_pollers_section() -> None:
    payload = TaskQueueInfo(
        namespace="default",
        task_queue="queue-1",
        pollers=[TaskQueuePoller(identity="worker-1", last_access_time="2026-01-02T03:04:00+00:00")],
    )

    text = task_queue_renderer.task_queue(payload)

    assert "## Task Queue" in text
    assert "## Pollers" in text
    assert "| identity | last_access_time |" in text
    assert "worker-1" in text


def test_task_queue_renders_pollers_section_when_empty() -> None:
    payload = TaskQueueInfo(namespace="default", task_queue="queue-1", pollers=[])

    text = task_queue_renderer.task_queue(payload)

    assert "## Task Queue" in text
    assert "## Pollers" in text
    assert "_No items._" in text


def test_search_attributes_renders_custom_and_system_sections() -> None:
    payload = SearchAttributesInfo(
        namespace="default",
        custom={"CustomKeyword": "KEYWORD"},
        system={"ExecutionStatus": "KEYWORD"},
    )

    text = task_queue_renderer.search_attributes(payload)

    assert "## Search Attributes" in text
    assert "### Custom" in text
    assert "### System" in text
    assert "CustomKeyword" in text
    assert "ExecutionStatus" in text


def test_search_attributes_renders_sections_when_empty() -> None:
    payload = SearchAttributesInfo(namespace="default", custom={}, system={})

    text = task_queue_renderer.search_attributes(payload)

    assert "## Search Attributes" in text
    assert "### Custom" in text
    assert "### System" in text
    assert "_No data._" in text
