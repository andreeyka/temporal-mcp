"""Tests for worker deployment renderers."""

from temporal_mcp.models import WorkerDeploymentDetail, WorkerDeploymentSummary
from temporal_mcp.renderers import worker_deployment_renderer


def test_worker_deployment_list_renders_table() -> None:
    text = worker_deployment_renderer.worker_deployment_list(
        [WorkerDeploymentSummary(name="payments-worker", create_time="2026-01-01T00:00:00Z")]
    )
    assert "## Worker Deployments" in text
    assert "| name | create_time |" in text
    assert "payments-worker" in text


def test_worker_deployment_detail_renders_detail_block() -> None:
    text = worker_deployment_renderer.worker_deployment_detail(
        WorkerDeploymentDetail(name="payments-worker", version_count=2)
    )
    assert "## Worker Deployment" in text
    assert "**version_count**" in text
    assert "2" in text
