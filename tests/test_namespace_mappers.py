"""Tests for namespace mappers."""

from types import SimpleNamespace

from temporal_mcp.mappers import namespace_mapper


class _FakeRetentionTTL:
    def ToSeconds(self):  # noqa: N802
        return 259200


class _FakeConfigWithRetention:
    workflow_execution_retention_ttl = _FakeRetentionTTL()

    def HasField(self, name):  # noqa: N802
        return name == "workflow_execution_retention_ttl"


class _FakeConfigNoRetention:
    def HasField(self, _name):  # noqa: N802
        return False


class _FakeNamespaceListEntry:
    namespace_info = SimpleNamespace(name="ns-1", state="Registered", description="test namespace")
    config = _FakeConfigWithRetention()


class _FakeDescribeNamespaceResp:
    namespace_info = SimpleNamespace(
        name="ns-2", state="Deprecated", description="desc", owner_email="owner@example.com"
    )
    config = _FakeConfigNoRetention()
    is_global_namespace = True


def test_namespace_summary_maps_list_entry() -> None:
    summary = namespace_mapper.namespace_summary(_FakeNamespaceListEntry())

    assert summary.name == "ns-1"
    assert summary.state == "Registered"
    assert summary.description == "test namespace"
    assert summary.retention_seconds == 259200


def test_namespace_detail_maps_describe_response() -> None:
    detail = namespace_mapper.namespace_detail(_FakeDescribeNamespaceResp())

    assert detail.name == "ns-2"
    assert detail.owner_email == "owner@example.com"
    assert detail.is_global is True
    assert detail.retention_seconds is None
