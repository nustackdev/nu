"""Special value check operations.

IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

Operations for checking special sentinel values (Empty, NaN).
"""

from __future__ import annotations

from everyshape.typing import is_empty, is_nan

from .core import UnaryOp


__all__ = [
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
]


class IsEmptyOp(UnaryOp[bool]):
    """Check if operand is Empty sentinel."""

    def _apply_op(self, operand: object) -> bool:
        return is_empty(operand)


class NotEmptyOp(UnaryOp[bool]):
    """Check if operand is NOT Empty sentinel."""

    def _apply_op(self, operand: object) -> bool:
        return not is_empty(operand)


class IsNaNOp(UnaryOp[bool]):
    """Check if operand is NaN sentinel."""

    def _apply_op(self, operand: object) -> bool:
        return is_nan(operand)


class NotNaNOp(UnaryOp[bool]):
    """Check if operand is NOT NaN sentinel."""

    def _apply_op(self, operand: object) -> bool:
        return not is_nan(operand)
