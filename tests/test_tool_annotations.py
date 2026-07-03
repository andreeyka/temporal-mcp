"""Tests for the tool-annotation factories."""

from temporal_mcp.tool_annotations import mutating, read_only, write


def test_read_only_hints():
    ann = read_only("List Workflows")
    assert ann.title == "List Workflows"
    assert ann.readOnlyHint is True
    assert ann.idempotentHint is True
    assert ann.openWorldHint is True


def test_write_is_non_destructive():
    ann = write("Start Workflow")
    assert ann.title == "Start Workflow"
    assert ann.readOnlyHint is False
    assert ann.destructiveHint is False
    assert ann.openWorldHint is True


def test_mutating_is_destructive():
    ann = mutating("Terminate Workflow")
    assert ann.title == "Terminate Workflow"
    assert ann.readOnlyHint is False
    assert ann.destructiveHint is True
    assert ann.idempotentHint is False
