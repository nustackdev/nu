"""Comparison base classes for Term types.

This module provides comparison operation mixins including:
- OrderableBase - __gt__, __lt__, __ge__, __le__
- EqualableBase - eq(), ne(), is_()
- ComparisonBase - Combines Orderable + Equalable
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from term.types import BoolType


__all__ = [
    "ComparisonBase",
    "EqualableBase",
    "OrderableBase",
]


class OrderableBase[OperandT]:
    """Base for values that support ordering comparisons: >, <, >=, <=."""

    def __gt__(self, other: OperandT) -> BoolType:
        """Greater than: self > other."""
        from term.ops import GtOp
        from term.types import BoolType

        return BoolType(GtOp(self, other))

    def __lt__(self, other: OperandT) -> BoolType:
        """Less than: self < other."""
        from term.ops import LtOp
        from term.types import BoolType

        return BoolType(LtOp(self, other))

    def __ge__(self, other: OperandT) -> BoolType:
        """Greater than or equal: self >= other."""
        from term.ops import GeOp
        from term.types import BoolType

        return BoolType(GeOp(self, other))

    def __le__(self, other: OperandT) -> BoolType:
        """Less than or equal: self <= other."""
        from term.ops import LeOp
        from term.types import BoolType

        return BoolType(LeOp(self, other))


class EqualableBase[OperandT]:
    """Base for values that support equality comparison.

    Note: == and != are blocked; use eq() and ne() methods.
    """

    def __eq__(self, other: object) -> bool:
        """Equality is blocked in DSL context.

        Raises:
            TypeError: Use eq() method instead
        """
        raise TypeError("Cannot use == directly on Terms. Use .eq(other) method instead.")

    def __ne__(self, other: object) -> bool:
        """Inequality is blocked in DSL context.

        Raises:
            TypeError: Use ne() method instead
        """
        raise TypeError("Cannot use != directly on Terms. Use .ne(other) method instead.")

    def eq(self, other: OperandT) -> BoolType:
        """Equality: self == other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from term.ops import EqOp
        from term.types import BoolType

        return BoolType(EqOp(self, other))

    def ne(self, other: OperandT) -> BoolType:
        """Inequality: self != other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from term.ops import NeOp
        from term.types import BoolType

        return BoolType(NeOp(self, other))

    def is_(self, other: OperandT) -> BoolType:
        """Identity comparison: self is other (safe method).

        Args:
            other: Value to compare id to

        Returns:
            IdCompOp expression
        """
        from term.ops import IdCompOp
        from term.types import BoolType

        return BoolType(IdCompOp(self, other))


class ComparisonBase[OperandT](
    OrderableBase[OperandT],
    EqualableBase[OperandT],
):
    """Full comparison operations: >, <, >=, <=, eq(), ne(), is_().

    Use this for most comparable types.
    """

    pass
