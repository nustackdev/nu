"""Special value check ops.

IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

Operations for checking special sentinel values (Empty, Invalid).
"""

from __future__ import annotations

from nu.terms import UnaryCalc, is_empty, is_invalid


__all__ = [
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
]


class IsEmptyOp(UnaryCalc[bool]):
    """Check if operand is Empty sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return is_empty(operand)


class NotEmptyOp(UnaryCalc[bool]):
    """Check if operand is NOT Empty sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return not is_empty(operand)


class IsNaNOp(UnaryCalc[bool]):
    """Check if operand is Invalid sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return is_invalid(operand)


class NotNaNOp(UnaryCalc[bool]):
    """Check if operand is NOT Invalid sentinel."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return not is_invalid(operand)
