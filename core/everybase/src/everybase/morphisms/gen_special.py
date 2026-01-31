"""Special value check morphisms.

IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

Operations for checking special sentinel values (Empty, Invalid).
"""

from __future__ import annotations

from everyabc import UnaryOperation, is_empty, is_invalid


__all__ = [
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
]


class IsEmptyOp(UnaryOperation[bool]):
    """Check if operand is Empty sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return is_empty(operand)


class NotEmptyOp(UnaryOperation[bool]):
    """Check if operand is NOT Empty sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return not is_empty(operand)


class IsNaNOp(UnaryOperation[bool]):
    """Check if operand is Invalid sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return is_invalid(operand)


class NotNaNOp(UnaryOperation[bool]):
    """Check if operand is NOT Invalid sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return not is_invalid(operand)
