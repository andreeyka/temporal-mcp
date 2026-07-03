"""Worker-deployment read tools are wired and stay visible under read-only mode."""

from tests.wiring_helpers import assert_reads_and_writes


def test_worker_deployment_wiring():
    assert_reads_and_writes(
        reads=("list_worker_deployments", "describe_worker_deployment"),
        writes=(),
    )
