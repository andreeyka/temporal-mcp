"""Tests for Nexus endpoint renderers."""

from temporal_mcp.models import NexusEndpointDetail, NexusEndpointSummary
from temporal_mcp.renderers import nexus_renderer


def test_nexus_endpoint_list_renders_table() -> None:
    text = nexus_renderer.nexus_endpoint_list(
        [NexusEndpointSummary(id="endpoint-1", name="payments", url_prefix="/pay")]
    )
    assert "## Nexus Endpoints" in text
    assert "| id | name | url_prefix | version | created_time |" in text
    assert "payments" in text


def test_nexus_endpoint_detail_renders_detail_block() -> None:
    text = nexus_renderer.nexus_endpoint_detail(
        NexusEndpointDetail(id="endpoint-1", name="payments", target={"namespace": "default"})
    )
    assert "## Nexus Endpoint" in text
    assert "**target**" in text
    assert "default" in text
