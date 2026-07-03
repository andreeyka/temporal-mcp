"""Shared pytest fixtures.

Isolates the test suite from the developer's local ``.env`` and any ambient
``MCP_*`` / ``TEMPORAL_*`` / ``IDP_*`` environment variables, so configuration
tests observe only the values a test explicitly provides.
"""

from __future__ import annotations

import os

import pytest
from pydantic_settings import BaseSettings


_SETTINGS_ENV_PREFIXES = ("MCP_", "TEMPORAL_", "IDP_")


def _live_settings_classes() -> list[type[BaseSettings]]:
    """Return every currently-alive ``BaseSettings`` subclass.

    Walks the subclass tree at call time (rather than caching) because some
    tests ``importlib.reload`` the config module, which leaves both the
    original and the reloaded settings classes alive and in use.

    Returns:
        A list of all live ``BaseSettings`` subclasses.
    """
    found: list[type[BaseSettings]] = []
    stack = list(BaseSettings.__subclasses__())
    while stack:
        settings_cls = stack.pop()
        found.append(settings_cls)
        stack.extend(settings_cls.__subclasses__())
    return found


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Detach settings from the local ``.env`` file and ambient env vars.

    Runs automatically for every test: strips configuration environment
    variables and forces every ``BaseSettings`` subclass to ignore its
    ``.env`` file, so a test only sees the values it constructs explicitly.

    Args:
        monkeypatch: Pytest patcher used to remove env vars and override the
            per-class ``env_file`` setting (both restored after the test).
    """
    for var in list(os.environ):
        if var.startswith(_SETTINGS_ENV_PREFIXES):
            monkeypatch.delenv(var, raising=False)
    for settings_cls in _live_settings_classes():
        monkeypatch.setitem(settings_cls.model_config, "env_file", None)
