from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .expression import Expression

__all__ = [
    "ExpressionError",
    "ValueResolutionError",
]


class ExpressionError(Exception):
    """Base exception for expression-related errors."""

    def __init__(
        self,
        message: str,
        *,
        expression: Optional["Expression"] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.expression = expression
        self.cause = cause


class ValueResolutionError(ExpressionError):
    """Raised when value resolution fails."""

    pass
