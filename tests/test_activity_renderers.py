"""Tests for activity renderers."""

from temporal_mcp.models import ActivityDetail, ActivitySummary
from temporal_mcp.renderers import activity_renderer


def test_activity_list_renders_table() -> None:
    text = activity_renderer.activity_list(
        [ActivitySummary(activity_id="a1", activity_run_id="run-1", activity_type="Act", status="RUNNING")]
    )
    assert "## Activities" in text
    assert "activity_run_id" in text
    assert "a1" in text
    assert "run-1" in text


def test_activity_detail_renders_detail_block() -> None:
    text = activity_renderer.activity_detail(ActivityDetail(activity_id="a1", attempt=3))
    assert "## Activity" in text
    assert "**attempt**" in text
    assert "3" in text
