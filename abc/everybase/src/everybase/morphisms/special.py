"""Special value check morphisms.

IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

Operations for checking special sentinel values (Empty, Invalid).
"""

from __future__ import annotations

from everyabc import Operation, UnaryMorphism, is_empty, is_invalid


__all__ = [
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
]


class IsEmptyOp(Operation, UnaryMorphism[bool]):
    """Check if operand is Empty sentinel."""

    def _apply(self, operand: object) -> bool:
        return is_empty(operand)


class NotEmptyOp(Operation, UnaryMorphism[bool]):
    """Check if operand is NOT Empty sentinel."""

    def _apply(self, operand: object) -> bool:
        return not is_empty(operand)


class IsNaNOp(Operation, UnaryMorphism[bool]):
    """Check if operand is Invalid sentinel."""

    def _apply(self, operand: object) -> bool:
        return is_invalid(operand)


class NotNaNOp(Operation, UnaryMorphism[bool]):
    """Check if operand is NOT Invalid sentinel."""

    def _apply(self, operand: object) -> bool:
        return not is_invalid(operand)
