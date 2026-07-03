"""The 4 schedule-control tools are wired into build() and hidden under read-only mode."""

from tests.wiring_helpers import assert_reads_and_writes


def test_schedule_control_wiring():
    assert_reads_and_writes(
        reads=(),
        writes=("create_schedule", "update_schedule", "trigger_schedule", "backfill_schedule"),
    )
