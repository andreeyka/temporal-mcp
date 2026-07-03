"""Tests for incoming JWT claim authorization expressions."""

import asyncio
import logging
from types import SimpleNamespace

import pytest
from fastmcp.server.auth import AccessToken

from temporal_mcp import middleware as middleware_module
from temporal_mcp.errors import IncomingAuthPolicyConfigError, IncomingAuthPolicyDeniedError
from temporal_mcp.middleware import ClaimExpressionMiddleware
from temporal_mcp.services.auth_policy import ClaimExpressionPolicy, parse_claim_expression


def _access(claims: dict[str, object]) -> AccessToken:
    return AccessToken(token="jwt", client_id="client", scopes=[], claims=claims)


def _request_context():
    return SimpleNamespace(message=object())


async def _return_ok(_context):
    return "ok"


def test_parse_claim_expression_returns_none_for_unset_value():
    assert parse_claim_expression(None) is None


def test_claim_expression_allows_matching_group():
    policy = parse_claim_expression('"Example-Admins" in groups || "Example-Operators" in groups')
    assert policy is not None
    assert policy.allows({"groups": ["Example-Admins"]}) is True


def test_claim_expression_rejects_non_matching_group():
    policy = ClaimExpressionPolicy('"Example-Admins" in groups')
    assert policy.allows({"groups": ["Other"]}) is False


def test_claim_expression_supports_boolean_logic():
    policy = ClaimExpressionPolicy('email_verified == true && "Example-Admins" in groups')
    claims = {"email_verified": True, "groups": ["Example-Admins"]}
    assert policy.allows(claims) is True


def test_claim_expression_supports_nested_claims():
    policy = ClaimExpressionPolicy('"admin" in realm_access.roles')
    claims = {"realm_access": {"roles": ["admin"]}}
    assert policy.allows(claims) is True


def test_claim_expression_ignores_hyphenated_top_level_claims():
    policy = ClaimExpressionPolicy('"Example-Admins" in groups')
    claims = {"allowed-origins": ["http://localhost:3000"], "groups": ["Example-Admins"]}
    assert policy.allows(claims) is True


def test_claim_expression_supports_claims_map_for_original_claim_names():
    policy = ClaimExpressionPolicy('"http://localhost:3000" in claims["allowed-origins"]')
    claims = {"allowed-origins": ["http://localhost:3000"]}
    assert policy.allows(claims) is True


def test_parse_claim_expression_rejects_invalid_syntax():
    with pytest.raises(IncomingAuthPolicyConfigError):
        parse_claim_expression('"Example-Admins" in')


def test_claim_expression_rejects_non_boolean_result():
    policy = ClaimExpressionPolicy('"not-a-bool"')
    assert policy.allows({}) is False


def test_claim_expression_middleware_allows_matching_claims(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    policy = ClaimExpressionPolicy('"Example-Admins" in groups')
    monkeypatch.setattr(middleware_module, "get_access_token", lambda: _access({"groups": ["Example-Admins"]}))
    result = asyncio.run(ClaimExpressionMiddleware(policy).on_request(_request_context(), _return_ok))
    assert result == "ok"
    assert "Incoming claim expression allowed request" in caplog.text


def test_claim_expression_middleware_denies_non_matching_claims(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    policy = ClaimExpressionPolicy('"Example-Admins" in groups')
    monkeypatch.setattr(middleware_module, "get_access_token", lambda: _access({"groups": ["Other"]}))
    with pytest.raises(IncomingAuthPolicyDeniedError):
        asyncio.run(ClaimExpressionMiddleware(policy).on_request(_request_context(), _return_ok))
    assert "Incoming claim expression denied request" in caplog.text
