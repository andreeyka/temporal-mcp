"""Mappers for task queue and search attribute SDK objects."""

from __future__ import annotations

from typing import Any, cast

from temporal_mcp.mappers.helpers import timestamp_to_iso
from temporal_mcp.models import SearchAttributesInfo, TaskQueueInfo, TaskQueuePoller


# Any is constrained to SDK/protobuf mapper boundaries with dynamic attributes.


def task_queue_info(namespace: str, task_queue: str, raw: object) -> TaskQueueInfo:
    """Map a task queue description response to a task queue model.

    Args:
        namespace: Temporal namespace.
        task_queue: Task queue name.
        raw: Task queue description response.

    Returns:
        The mapped task queue information.
    """
    response = cast("Any", raw)
    return TaskQueueInfo(
        namespace=namespace,
        task_queue=task_queue,
        pollers=[_poller_info(item) for item in response.pollers],
    )


def search_attributes_info(namespace: str, raw: object) -> SearchAttributesInfo:
    """Map a search attributes response to a search attributes model.

    Args:
        namespace: Temporal namespace.
        raw: Search attributes response.

    Returns:
        The mapped search attributes information.
    """
    response = cast("Any", raw)
    return SearchAttributesInfo(
        namespace=namespace,
        custom=_string_map(response.custom_attributes),
        system=_string_map(response.system_attributes),
    )


def _poller_info(raw: object) -> TaskQueuePoller:
    poller = cast("Any", raw)
    return TaskQueuePoller(identity=poller.identity, last_access_time=timestamp_to_iso(poller.last_access_time))


def _string_map(raw: object) -> dict[str, str]:
    return {key: str(value) for key, value in dict(cast("Any", raw)).items()}
