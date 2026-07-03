"""Render batch operation output models as Markdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporal_mcp.renderers.entity_renderer import EntityRenderer, RenderSpec


if TYPE_CHECKING:
    from temporal_mcp.models import BatchOperationDetail, BatchOperationSummary


_ENTITY_RENDERER = EntityRenderer()
_BATCH_OPERATION_COLUMNS = ("job_id", "state", "start_time", "close_time")
_BATCH_OPERATION_SPEC = RenderSpec(title="Batch Operations", columns=_BATCH_OPERATION_COLUMNS)


def batch_operation_list(items: list[BatchOperationSummary]) -> str:
    """Render batch operation summaries as Markdown.

    Args:
        items: Batch operation summaries to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.list(items, _BATCH_OPERATION_SPEC)


def batch_operation_detail(detail: BatchOperationDetail) -> str:
    """Render one batch operation as Markdown.

    Args:
        detail: Batch operation detail to render.

    Returns:
        The rendered Markdown section.
    """
    return _ENTITY_RENDERER.detail(detail, "Batch Operation")
