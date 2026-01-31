# ruff: noqa: D102
"""Set capability — protocols + bases + mutations.

SetLikeProtocol/Base = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
MutableSetProtocol/Base = SetLike + add/remove/discard

Follows Python's collections.abc.Set / MutableSet pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from .col_collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import BoolValue


__all__ = [
    "MutableSetBase",
    "MutableSetProtocol",
    "SetLikeBase",
    "SetLikeProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


class SetLikeProtocol[ElementT, ResultT](
    CollectionProtocol[ElementT, ResultT],
    Protocol,
):
    """Protocol for set values — like collections.abc.Set."""

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT: ...
    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT: ...
    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT: ...
    def symmetric_difference(
        self, other: set[ElementT] | frozenset[ElementT] | Term
    ) -> ResultT: ...
    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue: ...
    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue: ...
    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue: ...


class MutableSetProtocol[ElementT, ResultT](
    SetLikeProtocol[ElementT, ResultT],
    Protocol,
):
    """Protocol for mutable set values — like collections.abc.MutableSet."""

    def add(self, value: ElementT) -> ResultT: ...
    def remove(self, value: ElementT) -> ResultT: ...
    def discard(self, value: ElementT) -> ResultT: ...


# =============================================================================
# BASES
# =============================================================================


class SetLikeBase[ElementT, ResultT](
    CollectionBase[ElementT, ResultT],
):
    """Base for set values — like collections.abc.Set."""

    def _wrap_set_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set union."""
        from everybase.morphisms.abc_set import UnionOp

        return cast("ResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set intersection."""
        from everybase.morphisms.abc_set import IntersectionOp

        return cast("ResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set difference."""
        from everybase.morphisms.abc_set import DifferenceOp

        return cast("ResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set symmetric difference."""
        from everybase.morphisms.abc_set import SymmetricDifferenceOp

        return cast("ResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue:
        """Check if subset."""
        from everybase.morphisms.abc_set import IsSubsetOp
        from everybase.values import BoolValue

        return BoolValue(IsSubsetOp(self, other))

    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue:
        """Check if superset."""
        from everybase.morphisms.abc_set import IsSupersetOp
        from everybase.values import BoolValue

        return BoolValue(IsSupersetOp(self, other))

    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue:
        """Check if disjoint."""
        from everybase.morphisms.abc_set import IsDisjointOp
        from everybase.values import BoolValue

        return BoolValue(IsDisjointOp(self, other))


class MutableSetBase[ElementT, ResultT](
    SetLikeBase[ElementT, ResultT],
):
    """Base for mutable set values — like collections.abc.MutableSet."""

    def add(self, value: ElementT) -> ResultT:
        """Add element to set."""
        from everybase.morphisms.abc_set import AddCmd

        return cast("ResultT", self._wrap_set_result(AddCmd(self, value)))

    def remove(self, value: ElementT) -> ResultT:
        """Remove element from set. Returns INVALID if not found."""
        from everybase.morphisms.abc_set import RemoveCmd

        return cast("ResultT", self._wrap_set_result(RemoveCmd(self, value)))

    def discard(self, value: ElementT) -> ResultT:
        """Remove element if present (no error if absent)."""
        from everybase.morphisms.abc_set import DiscardCmd

        return cast("ResultT", self._wrap_set_result(DiscardCmd(self, value)))
