"""Tests for the Temporal MCP prompts."""

import asyncio

from temporal_mcp.prompts.prompts import (
    cluster_health_review,
    diagnose_workflow_failure,
    prompts_mcp,
    triage_namespace_failures,
)


EXPECTED = {"triage_namespace_failures", "diagnose_workflow_failure", "cluster_health_review"}


def test_all_prompts_registered():
    names = {p.name for p in asyncio.run(prompts_mcp.list_prompts())}
    assert names == EXPECTED


def test_diagnose_workflow_failure_mentions_inputs_and_sources():
    text = diagnose_workflow_failure("prod", "order-123")
    assert "order-123" in text
    assert "prod" in text
    assert "analyze_workflow_failure" in text
    assert "temporal://namespace/prod/failures" in text


def test_cluster_health_review_points_at_cluster_tools():
    text = cluster_health_review()
    assert "get_cluster_info" in text
    assert "list_namespaces" in text
    assert "summarize_namespace_failures" in text


def test_triage_prompt_still_works():
    assert "staging" in triage_namespace_failures("staging")
