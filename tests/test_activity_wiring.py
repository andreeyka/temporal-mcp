"""Activity read tools are wired and remain visible under read-only mode."""

from tests.wiring_helpers import assert_reads_and_writes


def test_activity_wiring():
    assert_reads_and_writes(
        reads=("list_activities", "describe_activity"),
        writes=(),
    )
