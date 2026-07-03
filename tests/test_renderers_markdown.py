"""Tests for Markdown and entity renderers."""

from pydantic import BaseModel

from temporal_mcp.models import (
    ActivitySummary,
    BatchOperationSummary,
    ExecutionSummary,
    NexusEndpointSummary,
    ScheduleSummary,
    WorkerDeploymentSummary,
)
from temporal_mcp.renderers import (
    activity_renderer,
    batch_renderer,
    markdown as md,
    nexus_renderer,
    schedule_renderer,
    worker_deployment_renderer,
    workflow_renderer,
)
from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


class Item(BaseModel):
    name: str
    status: str | None = None


def test_dict_block_renders_heading_and_bullets() -> None:
    text = md.dict_block({"workflow_id": "wf-1", "status": "RUNNING"}, "Workflow")
    assert "## Workflow" in text
    assert "**workflow_id**" in text
    assert "wf-1" in text


def test_cell_escapes_pipes_and_newlines() -> None:
    assert md.cell("a|b\nc") == "a\\|b c"


def test_cell_renders_none_as_em_dash() -> None:
    assert md.cell(None) == "—"


def test_heading_renders_level() -> None:
    assert md.heading("Workflow", level=3) == "### Workflow"


def test_table_renders_markdown_table() -> None:
    text = md.table(("name", "status"), [["alpha", "ok"]])
    assert text == "| name | status |\n| --- | --- |\n| alpha | ok |"


def test_kv_renders_empty_placeholder() -> None:
    assert md.kv({}) == "_No data._"


def test_entity_renderer_list_renders_model_table() -> None:
    text = EntityRenderer().list(
        [Item(name="alpha", status="ok")],
        RenderSpec(title="Items", columns=("name", "status")),
    )
    assert "## Items" in text
    assert "| name | status |" in text
    assert "alpha" in text


def test_entity_renderer_empty_list_uses_spec_text() -> None:
    text = EntityRenderer().list(
        [],
        RenderSpec(title="Items", columns=("name",), empty_text="Nothing here."),
    )
    assert "## Items" in text
    assert "_Nothing here._" in text


def test_dict_table_renders_titled_table() -> None:
    text = md.dict_table([{"name": "alpha", "status": "ok"}], "Items", columns=("name", "status"))
    assert text == "## Items\n\n| name | status |\n| --- | --- |\n| alpha | ok |"


def test_sections_joins_non_empty_parts() -> None:
    assert md.sections(["## One", "", "## Two"]) == "## One\n\n## Two"


def test_list_renderer_columns_cover_summary_model_fields() -> None:
    pairs = [
        (ExecutionSummary, workflow_renderer._EXEC_COLUMNS),
        (ActivitySummary, activity_renderer._ACTIVITY_COLUMNS),
        (BatchOperationSummary, batch_renderer._BATCH_OPERATION_COLUMNS),
        (NexusEndpointSummary, nexus_renderer._NEXUS_ENDPOINT_COLUMNS),
        (ScheduleSummary, schedule_renderer._SCHEDULE_COLUMNS),
        (WorkerDeploymentSummary, worker_deployment_renderer._WORKER_DEPLOYMENT_COLUMNS),
    ]

    for model, columns in pairs:
        assert set(model.model_fields) <= set(columns)
