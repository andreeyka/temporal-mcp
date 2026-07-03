"""Helpers for building MCP ToolResult payloads."""

from __future__ import annotations

import json
from typing import Any, cast

from fastmcp.tools import ToolResult
from mcp.types import TextContent
from pydantic import BaseModel

from temporal_mcp.models.action_models import ActionResult
from temporal_mcp.renderers import action_renderer


def to_jsonable(value: object) -> object:
    """Recursively convert values to JSON-serializable data.

    Args:
        value: Value to convert.

    Returns:
        The converted JSON-serializable value.
    """
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def _to_json_text_value(value: object) -> object:
    """Recursively convert values for human-readable JSON text rendering.

    Args:
        value: Value to convert.

    Returns:
        The converted value, preserving Python objects for ``json.dumps(default=str)``.
    """
    if isinstance(value, BaseModel):
        return _to_json_text_value(value.model_dump(mode="python"))
    if isinstance(value, dict):
        return {key: _to_json_text_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_json_text_value(item) for item in value]
    return value


def _to_jsonable_dict(value: dict[str, object]) -> dict[str, object]:
    """Convert a mapping payload to JSON-serializable data.

    Args:
        value: Mapping to convert.

    Returns:
        The converted mapping.
    """
    return {key: to_jsonable(item) for key, item in value.items()}


def to_json_text(value: object) -> str:
    """Render a value as indented JSON text.

    Args:
        value: Value to render.

    Returns:
        The formatted JSON string.
    """
    return json.dumps(_to_json_text_value(value), indent=2, ensure_ascii=False, default=str)


def make_tool_result(
    text: str,
    *,
    structured_content: bool = False,
    structured: object | None = None,
) -> ToolResult:
    """Build a ToolResult with Markdown text and optional structured JSON.

    Args:
        text: Human-readable Markdown text.
        structured_content: Whether to attach structured content.
        structured: Structured payload to attach.

    Returns:
        The tool result payload.
    """
    result = ToolResult(content=[TextContent(type="text", text=text)])
    if structured_content and structured is not None:
        converted = to_jsonable(structured)
        # Any mirrors FastMCP's ToolResult.structured_content type.
        result.structured_content = cast("dict[str, Any]", converted)
    return result


def make_action_result(
    payload: dict[str, object],
    title: str,
    *,
    structured_content: bool = False,
) -> ToolResult:
    """Render a mutation/action result and package it as a ToolResult.

    Args:
        payload: The action result fields.
        title: Markdown section title.
        structured_content: When True, attach ``{"result": result}`` as structured content.

    Returns:
        A ToolResult with Markdown text and optional structured content.
    """
    result = ActionResult.model_validate(payload)
    return make_tool_result(
        action_renderer.action_result(result, title),
        structured_content=structured_content,
        structured={"result": action_renderer.payload(result)},
    )
