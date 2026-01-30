"""Comparison capability traits for refs.

Atomic traits:
- Orderable: __gt__, __lt__, __ge__, __le__
- Equalable: eq(), ne(), is_()

Combined traits:
- Comparable = Orderable + Equalable
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everybase.py import BoolRef


__all__ = [
    "Comparable",
    "Equalable",
    "Orderable",
]


class Orderable[OperandT]:
    """Trait for values that support ordering comparisons: >, <, >=, <=."""

    def __gt__(self, other: OperandT) -> BoolRef:
        """Greater than: self > other."""
        from everybase.morphisms import GtOp
        from everybase.py import BoolRef

        return BoolRef(GtOp(self, other))

    def __lt__(self, other: OperandT) -> BoolRef:
        """Less than: self < other."""
        from everybase.morphisms import LtOp
        from everybase.py import BoolRef

        return BoolRef(LtOp(self, other))

    def __ge__(self, other: OperandT) -> BoolRef:
        """Greater than or equal: self >= other."""
        from everybase.morphisms import GeOp
        from everybase.py import BoolRef

        return BoolRef(GeOp(self, other))

    def __le__(self, other: OperandT) -> BoolRef:
        """Less than or equal: self <= other."""
        from everybase.morphisms import LeOp
        from everybase.py import BoolRef

        return BoolRef(LeOp(self, other))


class Equalable[OperandT]:
    """Trait for values that support equality comparison.

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

    def eq(self, other: OperandT) -> BoolRef:
        """Equality: self == other (safe method)."""
        from everybase.morphisms import EqOp
        from everybase.py import BoolRef

        return BoolRef(EqOp(self, other))

    def ne(self, other: OperandT) -> BoolRef:
        """Inequality: self != other (safe method)."""
        from everybase.morphisms import NeOp
        from everybase.py import BoolRef

        return BoolRef(NeOp(self, other))

    def is_(self, other: OperandT) -> BoolRef:
        """Identity comparison: self is other (safe method)."""
        from everybase.morphisms import IdCompOp
        from everybase.py import BoolRef

        return BoolRef(IdCompOp(self, other))


class Comparable[OperandT](
    Orderable[OperandT],
    Equalable[OperandT],
):
    """Full comparison: >, <, >=, <=, eq(), ne(), is_()."""

    pass
