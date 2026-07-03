"""Nexus read tools are wired and visible under read-only mode; writes are gated."""

from tests.wiring_helpers import assert_reads_and_writes


def test_nexus_wiring():
    assert_reads_and_writes(
        reads=("list_nexus_endpoints", "get_nexus_endpoint"),
        writes=("create_nexus_endpoint", "delete_nexus_endpoint"),
    )
