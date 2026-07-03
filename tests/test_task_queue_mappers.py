"""Tests for task queue mappers."""

from datetime import UTC, datetime
from types import SimpleNamespace

from temporal_mcp.mappers import task_queue_mapper
from temporal_mcp.models import SearchAttributesInfo, TaskQueueInfo


class FakeTimestamp:
    """Small fake protobuf timestamp for mapper tests."""

    def ToDatetime(self) -> datetime:  # noqa: N802
        """Return a deterministic datetime."""
        return datetime(2026, 1, 2, 3, 4, tzinfo=UTC)


def test_task_queue_info_maps_pollers() -> None:
    raw = SimpleNamespace(
        pollers=[
            SimpleNamespace(identity="worker-1", last_access_time=FakeTimestamp()),
            SimpleNamespace(identity="worker-2", last_access_time=None),
        ]
    )

    result = task_queue_mapper.task_queue_info("default", "queue-1", raw)

    assert isinstance(result, TaskQueueInfo)
    assert result.model_dump(mode="json") == {
        "namespace": "default",
        "task_queue": "queue-1",
        "pollers": [
            {"identity": "worker-1", "last_access_time": "2026-01-02T03:04:00+00:00"},
            {"identity": "worker-2", "last_access_time": None},
        ],
    }


def test_task_queue_info_handles_missing_pollers() -> None:
    result = task_queue_mapper.task_queue_info("default", "queue-1", SimpleNamespace(pollers=[]))

    assert result.pollers == []


def test_search_attributes_info_maps_attribute_values_to_strings() -> None:
    raw = SimpleNamespace(
        custom_attributes={"CustomKeyword": "KEYWORD"},
        system_attributes={"ExecutionStatus": 1},
    )

    result = task_queue_mapper.search_attributes_info("default", raw)

    assert isinstance(result, SearchAttributesInfo)
    assert result.model_dump(mode="json") == {
        "namespace": "default",
        "custom": {"CustomKeyword": "KEYWORD"},
        "system": {"ExecutionStatus": "1"},
    }
