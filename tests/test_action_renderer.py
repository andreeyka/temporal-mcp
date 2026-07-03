"""Tests for action result rendering."""

from temporal_mcp.models.action_models import ActionResult
from temporal_mcp.renderers import action_renderer


def test_action_result_renders_extra_fields() -> None:
    result = ActionResult(ok=True, workflow_id="wf-1")
    text = action_renderer.action_result(result, "Workflow Paused")
    assert "## Workflow Paused" in text
    assert "**ok**" in text
    assert "wf-1" in text


def test_action_result_omits_ok_when_unset() -> None:
    result = ActionResult.model_validate({"workflow_id": "wf-1"})
    text = action_renderer.action_result(result, "Workflow Paused")
    assert "**workflow_id**" in text
    assert "**ok**" not in text


def test_action_result_stringifies_python_mode_extra_object() -> None:
    class Marker:
        def __str__(self) -> str:
            return "marker-object"

    result = ActionResult.model_validate({"detail": Marker()})
    text = action_renderer.action_result(result, "Workflow Paused")
    assert "marker-object" in text
