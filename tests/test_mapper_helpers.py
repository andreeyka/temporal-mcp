"""Tests for mapper helper functions."""

from datetime import UTC, datetime
from types import SimpleNamespace

from temporal_mcp.mappers import helpers


class Timestamp:
    def ToDatetime(self):  # noqa: N802
        return datetime(2026, 1, 1, tzinfo=UTC)


class Message:
    start_time = Timestamp()

    def HasField(self, field):  # noqa: N802
        return field == "start_time"


def test_timestamp_field_to_iso_reads_present_proto_field():
    assert helpers.timestamp_field_to_iso(Message(), "start_time") == "2026-01-01T00:00:00+00:00"


def test_timestamp_field_to_iso_returns_none_for_missing_field():
    assert helpers.timestamp_field_to_iso(Message(), "close_time") is None


def test_timestamp_to_iso_converts_timestamp_or_none():
    assert helpers.timestamp_to_iso(Timestamp()) == "2026-01-01T00:00:00+00:00"
    assert helpers.timestamp_to_iso(None) is None


def test_enum_name_reads_name_attribute():
    assert helpers.enum_name(SimpleNamespace(name="RUNNING")) == "RUNNING"


def test_bytes_value_text_decodes_payload_data():
    assert helpers.bytes_value_text(SimpleNamespace(data=b"WorkflowA")) == "WorkflowA"
