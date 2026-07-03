"""Batch read tools stay visible under read-only mode; stop is hidden and gated."""

from tests.wiring_helpers import assert_reads_and_writes


def test_batch_wiring():
    assert_reads_and_writes(
        reads=("list_batch_operations", "describe_batch_operation"),
        writes=("stop_batch_operation",),
    )
