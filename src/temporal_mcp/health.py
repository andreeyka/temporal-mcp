"""Unauthenticated HTTP process health probe."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse


def register_health_route(app: FastMCP) -> None:
    """Register the process probe independently of Temporal access.

    Args:
        app: Server receiving the health route.
    """
    app.custom_route("/health", methods=["GET"], include_in_schema=False)(_health)


async def _health(_request: Request) -> JSONResponse:
    """Report process availability without calling upstream services."""
    return JSONResponse({"status": "ok"})
