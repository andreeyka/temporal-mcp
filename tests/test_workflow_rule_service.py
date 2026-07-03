"""Tests for the workflow-rule service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from temporal_mcp.services.workflow_rule_service import TemporalWorkflowRuleService


def _svc(client):
    pool = MagicMock()
    pool.get = AsyncMock(return_value=client)
    return TemporalWorkflowRuleService(pool)


def test_list_workflow_rules_builds_request_and_returns_list():
    resp = MagicMock()
    resp.rules = ["r0", "r1"]
    client = MagicMock()
    client.workflow_service.list_workflow_rules = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.list_workflow_rules("ns"))
    assert out == ["r0", "r1"]
    req = client.workflow_service.list_workflow_rules.call_args.args[0]
    assert req.namespace == "ns"


def test_describe_workflow_rule_returns_rule():
    resp = MagicMock(rule="RULE")
    client = MagicMock()
    client.workflow_service.describe_workflow_rule = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.describe_workflow_rule("ns", "rule-1"))
    assert out == "RULE"
    req = client.workflow_service.describe_workflow_rule.call_args.args[0]
    assert req.namespace == "ns"
    assert req.rule_id == "rule-1"


def test_create_workflow_rule_builds_spec_and_returns_id():
    resp = MagicMock()
    resp.rule.spec.id = "rule-1"
    client = MagicMock()
    client.workflow_service.create_workflow_rule = AsyncMock(return_value=resp)
    svc = _svc(client)
    out = asyncio.run(svc.create_workflow_rule("ns", "rule-1", "WorkflowType='foo'", description="d"))
    assert out == "rule-1"
    req = client.workflow_service.create_workflow_rule.call_args.args[0]
    assert req.namespace == "ns"
    assert req.spec.id == "rule-1"
    assert req.spec.visibility_query == "WorkflowType='foo'"
    assert req.description == "d"
    assert req.identity == "temporal-mcp"
    assert req.request_id


def test_create_workflow_rule_sets_expiration_when_given():
    resp = MagicMock()
    resp.rule.spec.id = "rule-1"
    client = MagicMock()
    client.workflow_service.create_workflow_rule = AsyncMock(return_value=resp)
    svc = _svc(client)
    asyncio.run(svc.create_workflow_rule("ns", "rule-1", "q", expiration="2026-01-01T00:00:00+00:00"))
    req = client.workflow_service.create_workflow_rule.call_args.args[0]
    assert req.spec.HasField("expiration_time")


def test_delete_workflow_rule_builds_request():
    client = MagicMock()
    client.workflow_service.delete_workflow_rule = AsyncMock(return_value=MagicMock())
    svc = _svc(client)
    asyncio.run(svc.delete_workflow_rule("ns", "rule-1"))
    req = client.workflow_service.delete_workflow_rule.call_args.args[0]
    assert req.namespace == "ns"
    assert req.rule_id == "rule-1"
