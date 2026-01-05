"""Comparison base classes for RValue types.

This module provides comparison operation mixins including:
- OrderableBase - __gt__, __lt__, __ge__, __le__
- EqualableBase - eq(), ne(), is_()
- ComparisonBase - Combines Orderable + Equalable
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..conversion import literal


if TYPE_CHECKING:
    from ..values import BoolValue


__all__ = [
    "ComparisonBase",
    "EqualableBase",
    "OrderableBase",
]


class OrderableBase[OperandT]:
    """Base for values that support ordering comparisons: >, <, >=, <=."""

    def __gt__(self, other: OperandT) -> BoolValue:
        """Greater than: self > other."""
        from ...comps.value.binary_ops import GtOp
        from ..values import BoolValue

        return BoolValue(GtOp(self, literal(other)))

    def __lt__(self, other: OperandT) -> BoolValue:
        """Less than: self < other."""
        from ...comps.value.binary_ops import LtOp
        from ..values import BoolValue

        return BoolValue(LtOp(self, literal(other)))

    def __ge__(self, other: OperandT) -> BoolValue:
        """Greater than or equal: self >= other."""
        from ...comps.value.binary_ops import GeOp
        from ..values import BoolValue

        return BoolValue(GeOp(self, literal(other)))

    def __le__(self, other: OperandT) -> BoolValue:
        """Less than or equal: self <= other."""
        from ...comps.value.binary_ops import LeOp
        from ..values import BoolValue

        return BoolValue(LeOp(self, literal(other)))


class EqualableBase[OperandT]:
    """Base for values that support equality comparison.

    Note: == and != are blocked; use eq() and ne() methods.
    """

    def __eq__(self, other: object) -> bool:
        """Equality is blocked in DSL context.

        Raises:
            TypeError: Use eq() method instead
        """
        raise TypeError("Cannot use == directly on RValues. Use .eq(other) method instead.")

    def __ne__(self, other: object) -> bool:
        """Inequality is blocked in DSL context.

        Raises:
            TypeError: Use ne() method instead
        """
        raise TypeError("Cannot use != directly on RValues. Use .ne(other) method instead.")

    def eq(self, other: OperandT) -> BoolValue:
        """Equality: self == other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ...comps.value.binary_ops import EqOp
        from ..values import BoolValue

        return BoolValue(EqOp(self, literal(other)))

    def ne(self, other: OperandT) -> BoolValue:
        """Inequality: self != other (safe method).

        Args:
            other: Value to compare

        Returns:
            Comparison result
        """
        from ...comps.value.binary_ops import NeOp
        from ..values import BoolValue

        return BoolValue(NeOp(self, literal(other)))

    def is_(self, other: object) -> BoolValue:
        """Identity comparison: self is other (safe method).

        Args:
            other: Value to compare id to

        Returns:
            IdCompOp expression
        """
        from ...comps.value.binary_ops import IdCompOp
        from ..values import BoolValue

        return BoolValue(IdCompOp(self, literal(other)))


class ComparisonBase[OperandT](
    OrderableBase[OperandT],
    EqualableBase[OperandT],
):
    """Full comparison operations: >, <, >=, <=, eq(), ne(), is_().

    Use this for most comparable types.
    """

    pass
