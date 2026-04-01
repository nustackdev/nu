# ruff: noqa: D102
"""Comparison capabilities — protocols + bases.

Atomic:
    OrderableProtocol/Base: __gt__, __lt__, __ge__, __le__
    EqualableProtocol/Base: eq(), ne(), is_()

Combined:
    ComparableProtocol/Base = Orderable + Equalable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from ..values import BoolValue


__all__ = [
    "ComparableBase",
    "ComparableProtocol",
    "EqualableBase",
    "EqualableProtocol",
    "OrderableBase",
    "OrderableProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


@runtime_checkable
class OrderableProtocol[OperandT](Protocol):
    """Protocol for values that support ordering comparisons."""

    def __gt__(self, other: OperandT) -> BoolValue: ...
    def __lt__(self, other: OperandT) -> BoolValue: ...
    def __ge__(self, other: OperandT) -> BoolValue: ...
    def __le__(self, other: OperandT) -> BoolValue: ...


@runtime_checkable
class EqualableProtocol[OperandT](Protocol):
    """Protocol for values that support equality comparison."""

    def eq(self, other: OperandT) -> BoolValue: ...
    def ne(self, other: OperandT) -> BoolValue: ...
    def is_(self, other: OperandT) -> BoolValue: ...


class ComparableProtocol[OperandT](
    OrderableProtocol[OperandT],
    EqualableProtocol[OperandT],
    Protocol,
):
    """Full comparison protocol."""

    ...


# =============================================================================
# BASES
# =============================================================================


class OrderableBase[OperandT]:
    """Base for values that support ordering comparisons: >, <, >=, <=."""

    def __gt__(self, other: OperandT) -> BoolValue:
        """Greater than: self > other."""
        from nu.ops import GtOp
        from ..values import BoolValue

        return BoolValue(GtOp(self, other))

    def __lt__(self, other: OperandT) -> BoolValue:
        """Less than: self < other."""
        from nu.ops import LtOp
        from ..values import BoolValue

        return BoolValue(LtOp(self, other))

    def __ge__(self, other: OperandT) -> BoolValue:
        """Greater than or equal: self >= other."""
        from nu.ops import GeOp
        from ..values import BoolValue

        return BoolValue(GeOp(self, other))

    def __le__(self, other: OperandT) -> BoolValue:
        """Less than or equal: self <= other."""
        from nu.ops import LeOp
        from ..values import BoolValue

        return BoolValue(LeOp(self, other))


class EqualableBase[OperandT]:
    """Base for values that support equality comparison.

    Python ``==``/``!=`` use default identity semantics.
    Use ``.eq()`` / ``.ne()`` for DSL-level equality that builds
    expression trees.
    """

    def eq(self, other: OperandT) -> BoolValue:
        """Equality: self == other (safe method)."""
        from nu.ops import EqOp
        from ..values import BoolValue

        return BoolValue(EqOp(self, other))

    def ne(self, other: OperandT) -> BoolValue:
        """Inequality: self != other (safe method)."""
        from nu.ops import NeOp
        from ..values import BoolValue

        return BoolValue(NeOp(self, other))

    def is_(self, other: OperandT) -> BoolValue:
        """Identity comparison: self is other (safe method)."""
        from nu.ops import IdCompOp
        from ..values import BoolValue

        return BoolValue(IdCompOp(self, other))


class ComparableBase[OperandT](
    OrderableBase[OperandT],
    EqualableBase[OperandT],
):
    """Full comparison: >, <, >=, <=, eq(), ne(), is_()."""

    pass
