"""Generic entity renderers built on shared Markdown helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from temporal_mcp.renderers import markdown as md


if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydantic import BaseModel


@dataclass(frozen=True)
class RenderSpec:
    """Configuration for rendering entity collections.

    Attributes:
        title: Section title.
        columns: Ordered columns to render.
        empty_text: Fallback text for empty collections.
    """

    title: str
    columns: tuple[str, ...]
    empty_text: str = "No items."


class EntityRenderer:
    """Render Pydantic entities as Markdown tables or detail blocks."""

    def list(self, items: Sequence[BaseModel], spec: RenderSpec) -> str:
        """Render a sequence of models as a Markdown table.

        Args:
            items: Models to render.
            spec: Rendering configuration.

        Returns:
            The rendered Markdown section.
        """
        if not items:
            return f"{md.heading(spec.title)}\n\n_{spec.empty_text}_"
        rows = [item.model_dump(mode="json") for item in items]
        return md.dict_table(rows, spec.title, columns=spec.columns)

    def detail(self, item: BaseModel, title: str) -> str:
        """Render one model as a Markdown detail block.

        Args:
            item: Model to render.
            title: Section title.

        Returns:
            The rendered Markdown section.
        """
        return md.dict_block(item.model_dump(mode="json"), title)
