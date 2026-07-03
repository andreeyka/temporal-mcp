from temporal_mcp.utils.tool_output import make_action_result, make_tool_result


def test_make_tool_result_keeps_text_and_structured_payload() -> None:
    result = make_tool_result("## Payload", structured_content=True, structured={"items": [{"id": "one"}]})

    assert result.content[0].text == "## Payload"
    assert result.structured_content == {"items": [{"id": "one"}]}


def test_make_action_result_renders_and_packages():
    result = make_action_result({"ok": True, "workflow_id": "wf-1"}, "Workflow Started", structured_content=True)
    text = result.content[0].text
    assert "Workflow Started" in text
    assert "wf-1" in text
    assert result.structured_content == {"result": {"ok": True, "workflow_id": "wf-1"}}


def test_make_action_result_omits_structured_when_off():
    result = make_action_result({"ok": True}, "Done", structured_content=False)
    assert result.structured_content is None


def test_make_action_result_omits_ok_when_not_supplied() -> None:
    result = make_action_result({"workflow_id": "wf-1", "run_id": "r-1"}, "Workflow Started", structured_content=True)
    text = result.content[0].text
    assert "**ok**" not in text
    assert result.structured_content == {"result": {"workflow_id": "wf-1", "run_id": "r-1"}}


def test_make_action_result_renders_python_object_extra() -> None:
    class Marker:
        def __str__(self) -> str:
            return "marker-object"

    result = make_action_result({"detail": Marker()}, "Done", structured_content=False)
    assert "marker-object" in result.content[0].text
