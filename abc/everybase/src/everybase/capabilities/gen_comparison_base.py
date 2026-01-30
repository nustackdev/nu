"""Comparison capability bases.

Atomic:
    OrderableBase: __gt__, __lt__, __ge__, __le__
    EqualableBase: eq(), ne(), is_()

Combined:
    ComparableBase = Orderable + Equalable
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everybase.values import BoolValue


__all__ = [
    "ComparableBase",
    "EqualableBase",
    "OrderableBase",
]


class OrderableBase[OperandT]:
    """Base for values that support ordering comparisons: >, <, >=, <=."""

    def __gt__(self, other: OperandT) -> BoolValue:
        """Greater than: self > other."""
        from everybase.morphisms import GtOp
        from everybase.values import BoolValue

        return BoolValue(GtOp(self, other))

    def __lt__(self, other: OperandT) -> BoolValue:
        """Less than: self < other."""
        from everybase.morphisms import LtOp
        from everybase.values import BoolValue

        return BoolValue(LtOp(self, other))

    def __ge__(self, other: OperandT) -> BoolValue:
        """Greater than or equal: self >= other."""
        from everybase.morphisms import GeOp
        from everybase.values import BoolValue

        return BoolValue(GeOp(self, other))

    def __le__(self, other: OperandT) -> BoolValue:
        """Less than or equal: self <= other."""
        from everybase.morphisms import LeOp
        from everybase.values import BoolValue

        return BoolValue(LeOp(self, other))


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

    def eq(self, other: OperandT) -> BoolValue:
        """Equality: self == other (safe method)."""
        from everybase.morphisms import EqOp
        from everybase.values import BoolValue

        return BoolValue(EqOp(self, other))

    def ne(self, other: OperandT) -> BoolValue:
        """Inequality: self != other (safe method)."""
        from everybase.morphisms import NeOp
        from everybase.values import BoolValue

        return BoolValue(NeOp(self, other))

    def is_(self, other: OperandT) -> BoolValue:
        """Identity comparison: self is other (safe method)."""
        from everybase.morphisms import IdCompOp
        from everybase.values import BoolValue

        return BoolValue(IdCompOp(self, other))


class ComparableBase[OperandT](
    OrderableBase[OperandT],
    EqualableBase[OperandT],
):
    """Full comparison: >, <, >=, <=, eq(), ne(), is_()."""

    pass
