"""Tests for batch operation renderers."""

from temporal_mcp.models import BatchOperationDetail, BatchOperationSummary
from temporal_mcp.renderers import batch_renderer


def test_batch_operation_list_renders_table() -> None:
    text = batch_renderer.batch_operation_list([BatchOperationSummary(job_id="job-1", state="RUNNING")])
    assert "## Batch Operations" in text
    assert "| job_id | state | start_time | close_time |" in text
    assert "job-1" in text


def test_batch_operation_detail_renders_detail_block() -> None:
    text = batch_renderer.batch_operation_detail(BatchOperationDetail(job_id="job-1", total_operation_count=7))
    assert "## Batch Operation" in text
    assert "**total_operation_count**" in text
    assert "7" in text
