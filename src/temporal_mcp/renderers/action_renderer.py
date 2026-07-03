"""Render action and mutation results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers import markdown as md


if TYPE_CHECKING:
    from temporal_mcp.models.action_models import ActionResult


def payload(result: ActionResult) -> dict[str, object]:
    """Build the action payload used for rendering and structured output.

    Args:
        result: Action result model.

    Returns:
        The action payload without unset fields.
    """
    return result.model_dump(mode="python", exclude_unset=True)


def action_result(result: ActionResult, title: str) -> str:
    """Render an action result as Markdown.

    Args:
        result: Action result model.
        title: Section title.

    Returns:
        The rendered Markdown section.
    """
    return md.dict_block(payload(result), title)
