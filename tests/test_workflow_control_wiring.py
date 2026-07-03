"""The 5 control tools are wired into build() and hidden under read-only mode."""

from tests.wiring_helpers import assert_reads_and_writes


def test_workflow_control_wiring():
    assert_reads_and_writes(
        reads=(),
        writes=(
            "pause_workflow",
            "unpause_workflow",
            "signal_with_start_workflow",
            "update_workflow",
            "reset_workflow",
        ),
    )
