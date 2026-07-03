"""Incoming JWT claim authorization expression support."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import celpy
from celpy import celtypes

from temporal_mcp.errors import IncomingAuthPolicyConfigError


if TYPE_CHECKING:
    from collections.abc import Mapping

    from celpy.adapter import JSON
    from celpy.evaluation import Context


logger = logging.getLogger(__name__)
_VALID_CEL_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CLAIMS_MAP_NAME = "claims"


class ClaimExpressionPolicy:
    """Compiled CEL expression for incoming JWT claim authorization."""

    def __init__(self, expression: str) -> None:
        """Compile a CEL expression.

        Args:
            expression: CEL expression evaluated against JWT claims.

        Raises:
            IncomingAuthPolicyConfigError: If the expression cannot be compiled.
        """
        self.expression = expression
        environment = celpy.Environment()
        try:
            ast = environment.compile(expression)
        except celpy.CELParseError as exc:
            raise IncomingAuthPolicyConfigError(str(exc)) from None
        self._program = environment.program(ast)

    def allows(self, claims: Mapping[str, object]) -> bool:
        """Return whether claims satisfy this expression.

        Args:
            claims: Verified JWT claims to authorize.

        Returns:
            True when the expression evaluates to boolean true; otherwise false.
        """
        try:
            result = self._program.evaluate(_claims_activation(claims))
        except celpy.CELEvalError:
            return False
        if not isinstance(result, celtypes.BoolType):
            logger.info("Bearer token rejected: incoming claim expression returned a non-boolean result")
            return False
        return bool(result)


def parse_claim_expression(raw_expression: str | None) -> ClaimExpressionPolicy | None:
    """Parse an optional CEL incoming claim expression.

    Args:
        raw_expression: CEL expression string from configuration.

    Returns:
        Compiled claim expression policy, or None when no expression is configured.

    Raises:
        IncomingAuthPolicyConfigError: If the expression syntax is invalid.
    """
    if raw_expression is None or not raw_expression.strip():
        return None
    return ClaimExpressionPolicy(raw_expression)


def _claims_activation(claims: Mapping[str, object]) -> Context:
    """Convert JWT claims to CEL values keyed by claim name."""
    activation = {_CLAIMS_MAP_NAME: celpy.json_to_cel(_json_claim(dict(claims)))}
    activation.update(_identifier_claims(claims))
    return activation


def _identifier_claims(claims: Mapping[str, object]) -> Context:
    """Return CEL identifier-compatible top-level claims."""
    return {name: celpy.json_to_cel(_json_claim(value)) for name, value in claims.items() if _is_identifier_claim(name)}


def _is_identifier_claim(name: str) -> bool:
    """Return whether the claim can be exposed as a CEL identifier."""
    return name != _CLAIMS_MAP_NAME and _VALID_CEL_IDENTIFIER.fullmatch(name) is not None


def _json_claim(value: object) -> JSON:
    """Return a JSON-compatible claim value for CEL conversion."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list):
        return [_json_claim(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_claim(item) for key, item in value.items()}
    return None
