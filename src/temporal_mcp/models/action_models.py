"""Pydantic models for action and mutation results."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ActionResult(BaseModel):
    """Generic action result with optional extra result fields."""

    model_config = ConfigDict(extra="allow")

    ok: Annotated[bool | None, Field(description="Whether the action completed successfully.")] = None
