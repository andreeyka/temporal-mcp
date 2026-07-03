import pytest

from temporal_mcp.errors import (
    TemporalAuthError,
    TemporalConnectionError,
    TemporalMcpError,
    TokenExchangeError,
    UnknownWorkflowStatusError,
)


def test_hierarchy_and_messages():
    assert issubclass(UnknownWorkflowStatusError, TemporalMcpError)
    err = UnknownWorkflowStatusError("bogus", ["FAILED", "RUNNING"])
    assert "bogus" in str(err)
    assert "FAILED" in str(err)


def test_connection_detail():
    assert "boom" in str(TemporalConnectionError("h:7233", detail="boom"))
    assert "h:7233" in str(TemporalConnectionError("h:7233"))


def test_auth_and_exchange():
    assert isinstance(TemporalAuthError("nope"), TemporalMcpError)
    assert isinstance(TokenExchangeError(detail="x"), TemporalMcpError)
    with pytest.raises(TemporalMcpError):
        raise TemporalAuthError("nope")


def test_missing_auth_verifier_error_carries_mode():
    from temporal_mcp.errors import MissingAuthVerifierError, TemporalMcpError

    err = MissingAuthVerifierError("passthrough")
    assert isinstance(err, TemporalMcpError)
    assert err.auth_mode == "passthrough"
    assert "passthrough" in str(err)


def test_incoming_auth_config_error_names_missing_var():
    from temporal_mcp.errors import IncomingAuthConfigError

    err = IncomingAuthConfigError("keycloak", "IDP_ISSUER")
    assert err.mode == "keycloak"
    assert err.missing == "IDP_ISSUER"
    assert "IDP_ISSUER" in str(err)
    assert "keycloak" in str(err)


def test_domain_errors_are_fastmcp_tool_errors():
    from fastmcp.exceptions import ToolError

    from temporal_mcp.errors import TemporalMcpError, UnknownWorkflowStatusError

    assert issubclass(TemporalMcpError, ToolError)
    err = UnknownWorkflowStatusError("BOGUS", ["RUNNING"])
    assert isinstance(err, ToolError)
    assert err.message == str(err)


def test_rpc_error_base_carries_status_and_detail():
    from temporal_mcp.errors import TemporalRpcError

    err = TemporalRpcError("boom", status_name="NOT_FOUND", detail="boom")
    assert isinstance(err, TemporalMcpError)
    assert err.status_name == "NOT_FOUND"
    assert err.detail == "boom"


def test_unsupported_server_feature_error_includes_hint():
    from temporal_mcp.errors import TemporalRpcError, UnsupportedServerFeatureError

    err = UnsupportedServerFeatureError("unknown method ListActivityExecutions", hint="needs 1.31.0")
    assert isinstance(err, TemporalRpcError)
    assert err.status_name == "UNIMPLEMENTED"
    assert "unknown method ListActivityExecutions" in str(err)
    assert "needs 1.31.0" in str(err)
    assert err.hint == "needs 1.31.0"


def test_simple_rpc_errors_pass_detail_through():
    from temporal_mcp.errors import TemporalAlreadyExistsError, TemporalNotFoundError, TemporalRateLimitedError

    assert "no such wf" in str(TemporalNotFoundError("no such wf"))
    assert "dup schedule" in str(TemporalAlreadyExistsError("dup schedule"))
    assert "quota" in str(TemporalRateLimitedError("quota"))
    assert TemporalNotFoundError("x").status_name == "NOT_FOUND"
    assert TemporalAlreadyExistsError("x").status_name == "ALREADY_EXISTS"
    assert TemporalRateLimitedError("x").status_name == "RESOURCE_EXHAUSTED"


def test_status_named_rpc_errors_embed_status():
    from temporal_mcp.errors import TemporalInvalidRequestError, TemporalPermissionDeniedError, TemporalUnavailableError

    inv = TemporalInvalidRequestError("INVALID_ARGUMENT", "bad query")
    assert "INVALID_ARGUMENT" in str(inv)
    assert "bad query" in str(inv)
    assert inv.status_name == "INVALID_ARGUMENT"
    assert "UNAUTHENTICATED" in str(TemporalPermissionDeniedError("UNAUTHENTICATED", "no token"))
    assert "UNAVAILABLE" in str(TemporalUnavailableError("UNAVAILABLE", "conn refused"))
