"""Workflow-rule tools are wired; reads stay visible under read-only, writes/deletes do not."""

from tests.wiring_helpers import assert_reads_and_writes


def test_workflow_rule_wiring():
    assert_reads_and_writes(
        reads=("list_workflow_rules", "describe_workflow_rule"),
        writes=("create_workflow_rule", "delete_workflow_rule"),
    )
