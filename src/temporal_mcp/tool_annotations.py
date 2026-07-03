"""ToolAnnotations factories hinting client behavior."""

from mcp.types import ToolAnnotations


def read_only(title: str) -> ToolAnnotations:
    """Build annotations for a safe, idempotent read tool.

    Args:
        title: Human-readable tool title.

    Returns:
        ToolAnnotations marking a read-only operation.
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )


def write(title: str) -> ToolAnnotations:
    """Build annotations for an additive / reversible write tool.

    Args:
        title: Human-readable tool title.

    Returns:
        ToolAnnotations marking a non-destructive state change.
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=False,
        openWorldHint=True,
    )


def mutating(title: str) -> ToolAnnotations:
    """Build annotations for a destructive, non-idempotent tool.

    Args:
        title: Human-readable tool title.

    Returns:
        ToolAnnotations marking a destructive state change.
    """
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    )
