"""Shared Markdown rendering helpers for tool text output."""

from __future__ import annotations


def cell(value: object) -> str:
    """Render one table cell for Markdown output.

    Args:
        value: Value to render.

    Returns:
        The escaped cell text.
    """
    if value is None:
        return "—"
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def heading(title: str, level: int = 2) -> str:
    """Build a Markdown heading line.

    Args:
        title: Heading text.
        level: Markdown heading level.

    Returns:
        The Markdown heading line.
    """
    return f"{'#' * level} {title}"


def table(headers: tuple[str, ...], rows: list[list[object]]) -> str:
    """Render a Markdown table.

    Args:
        headers: Ordered table headers.
        rows: Table rows matching the headers.

    Returns:
        The rendered Markdown table.
    """
    head = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(cell(item) for item in row) + " |" for row in rows]
    return "\n".join([head, separator, *body])


def kv(data: dict[str, object]) -> str:
    """Render key/value pairs as Markdown bullets.

    Args:
        data: Mapping to render.

    Returns:
        The rendered bullet list.
    """
    lines = [f"- **{key}**: {cell(value)}" for key, value in data.items()]
    return "\n".join(lines) if lines else "_No data._"


def dict_block(data: dict[str, object], title: str | None = None) -> str:
    """Render a detail block with an optional heading.

    Args:
        data: Record to render.
        title: Optional section title.

    Returns:
        The rendered Markdown block.
    """
    parts = [heading(title), "", kv(data)] if title else [kv(data)]
    return "\n".join(parts)


def dict_table(items: list[dict[str, object]], title: str, *, columns: tuple[str, ...]) -> str:
    """Render titled records as a Markdown table.

    Args:
        items: Records to render.
        title: Section title.
        columns: Ordered columns to include.

    Returns:
        The rendered Markdown section.
    """
    if not items:
        return f"{heading(title)}\n\n_No items._"
    rows = [[record.get(column) for column in columns] for record in items]
    return f"{heading(title)}\n\n{table(columns, rows)}"


def sections(parts: list[str]) -> str:
    """Join non-empty Markdown sections.

    Args:
        parts: Sections to join.

    Returns:
        The combined Markdown text.
    """
    return "\n\n".join(part for part in parts if part)
