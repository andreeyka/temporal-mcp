"""Resources are registered and remain available under read-only mode."""

import asyncio

from temporal_mcp.config import McpServerConfig
from temporal_mcp.main import build


STATIC_URI = "temporal://namespaces"
TEMPLATE_URI = "temporal://namespace/{ns}/failures"


def _static_uris(app):
    return {str(r.uri) for r in asyncio.run(app.list_resources())}


def _template_uris(app):
    return {t.uri_template for t in asyncio.run(app.list_resource_templates())}


def test_resources_registered_in_full_build():
    app = asyncio.run(build(McpServerConfig()))
    assert STATIC_URI in _static_uris(app)
    assert TEMPLATE_URI in _template_uris(app)


def test_resources_available_under_read_only():
    app = asyncio.run(build(McpServerConfig(read_only=True)))
    assert STATIC_URI in _static_uris(app)
    assert TEMPLATE_URI in _template_uris(app)


def test_resources_declare_json_mime_type():
    app = asyncio.run(build(McpServerConfig()))
    static = next(r for r in asyncio.run(app.list_resources()) if str(r.uri) == STATIC_URI)
    template = next(t for t in asyncio.run(app.list_resource_templates()) if t.uri_template == TEMPLATE_URI)
    assert static.mime_type == "application/json"
    assert template.mime_type == "application/json"


def test_prompts_still_present():
    app = asyncio.run(build(McpServerConfig()))
    names = {p.name for p in asyncio.run(app.list_prompts())}
    assert {"diagnose_workflow_failure", "cluster_health_review"} <= names
