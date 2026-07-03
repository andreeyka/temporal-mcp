"""Shared helpers for converting Temporal SDK and protobuf values."""

from __future__ import annotations

from typing import Any


# Any is constrained to SDK/protobuf mapper boundaries with dynamic attributes.


def iso_datetime(value: Any) -> str | None:  # noqa: ANN401
    """Return an ISO-8601 string for a datetime-like value."""
    return value.isoformat() if value is not None else None


def timestamp_field_to_iso(message: Any, field: str) -> str | None:  # noqa: ANN401
    """Return an ISO-8601 timestamp for a present protobuf timestamp field."""
    if not message.HasField(field):
        return None
    return getattr(message, field).ToDatetime().isoformat()


def timestamp_to_iso(value: Any) -> str | None:  # noqa: ANN401
    """Return an ISO-8601 timestamp for a protobuf timestamp value."""
    return value.ToDatetime().isoformat() if value is not None else None


def enum_name(value: Any) -> str | None:  # noqa: ANN401
    """Return the ``name`` attribute of an enum-like value."""
    return getattr(value, "name", None) if value is not None else None


def proto_enum_name(message: Any, field: str) -> str:  # noqa: ANN401
    """Return the enum value name for a protobuf enum field."""
    descriptor = message.DESCRIPTOR.fields_by_name[field]
    return descriptor.enum_type.values_by_number[getattr(message, field)].name


def oneof_name(message: Any, field: str) -> str | None:  # noqa: ANN401
    """Return the populated oneof variant name."""
    return message.WhichOneof(field)


def bytes_value_text(value: Any) -> str:  # noqa: ANN401
    """Decode a Temporal payload-like value to text."""
    data = getattr(value, "data", value)
    return data.decode("utf-8", "ignore") if isinstance(data, bytes) else str(data)
