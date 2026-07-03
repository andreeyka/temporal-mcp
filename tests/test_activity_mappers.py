"""Tests for activity mappers."""

from datetime import UTC, datetime
from types import SimpleNamespace

from temporal_mcp.mappers import activity_mapper as mapper
from temporal_mcp.models import ActivityDetail, ActivitySummary


def _fake_execution():
    return SimpleNamespace(
        activity_id="a1",
        activity_run_id="r1",
        activity_type="MyActivity",
        status=SimpleNamespace(name="RUNNING"),
        task_queue="tq",
        scheduled_time=datetime(2026, 1, 1, tzinfo=UTC),
        close_time=None,
    )


def _fake_detail():
    return SimpleNamespace(
        **vars(_fake_execution()),
        attempt=3,
        run_state=SimpleNamespace(name="STARTED"),
        paused=False,
        last_heartbeat_time=datetime(2026, 1, 2, tzinfo=UTC),
        last_failure=None,
    )


def test_activity_summary_shapes_fields():
    summary = mapper.activity_summary(_fake_execution())
    assert isinstance(summary, ActivitySummary)
    assert summary.activity_id == "a1"
    assert summary.status == "RUNNING"
    assert summary.scheduled_time == datetime(2026, 1, 1, tzinfo=UTC).isoformat()
    assert summary.close_time is None


def test_activity_detail_adds_diagnostics():
    detail = mapper.activity_detail(_fake_detail())
    assert isinstance(detail, ActivityDetail)
    assert detail.model_dump(mode="json", include={"attempt", "run_state", "paused"}) == {
        "attempt": 3,
        "run_state": "STARTED",
        "paused": False,
    }
    assert detail.last_heartbeat_time == datetime(2026, 1, 2, tzinfo=UTC).isoformat()
    assert detail.last_failure is None


def test_activity_summaries_maps_each_execution():
    summaries = mapper.activity_summaries([_fake_execution()])
    assert summaries == [mapper.activity_summary(_fake_execution())]
