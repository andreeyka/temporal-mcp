from temporal_mcp.tools.schedule_tools import temporal_schedule_mcp
from temporal_mcp.tools.task_queue_tools import temporal_task_queue_mcp


def test_providers_exist():
    assert temporal_schedule_mcp is not None
    assert temporal_task_queue_mcp is not None
