"""Shared MCP tool parameter aliases."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field


StructuredContent = Annotated[bool, Field(description="Return structured content for programmatic use.")]
