# ruff: noqa: D102
"""Set collection — protocols + bases + mutations.

SetLikeProtocol/Base = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
MutableSetProtocol/Base = SetLike + add/remove/discard

Follows Python's collections.abc.Set / MutableSet pattern.

Type Parameters:
    CollectionT: Native Python collection type (set[int], frozenset[str], etc.)
    ElementT: Native Python element type (int, str, etc.)
    CollectionResultT: Wrapped result for collection-level operations
        (union, intersection, difference, symmetric_difference, add, remove, discard)
    ElementResultT: Wrapped result for element-level operations
        (sum_, min_, max_)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from ..capabilities.col_collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from everybase.core import Term

    from ..values import BoolValue


__all__ = [
    "MutableSetBase",
    "MutableSetProtocol",
    "SetLikeBase",
    "SetLikeProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


class SetLikeProtocol[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionProtocol[ElementT, CollectionResultT, ElementResultT],
    Protocol,
):
    """Protocol for set values — like collections.abc.Set.

    Type Parameters:
        CollectionT: Native Python collection type (set[int], frozenset[str])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (union, intersection, ...)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> CollectionResultT: ...
    def intersection(
        self, other: set[ElementT] | frozenset[ElementT] | Term
    ) -> CollectionResultT: ...
    def difference(
        self, other: set[ElementT] | frozenset[ElementT] | Term
    ) -> CollectionResultT: ...
    def symmetric_difference(
        self, other: set[ElementT] | frozenset[ElementT] | Term
    ) -> CollectionResultT: ...
    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue: ...
    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue: ...
    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue: ...


class MutableSetProtocol[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SetLikeProtocol[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Protocol,
):
    """Protocol for mutable set values — like collections.abc.MutableSet.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (add, remove, discard)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    def add(self, value: ElementT) -> CollectionResultT: ...
    def remove(self, value: ElementT) -> CollectionResultT: ...
    def discard(self, value: ElementT) -> CollectionResultT: ...


# =============================================================================
# BASES
# =============================================================================


class SetLikeBase[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionBase[ElementT, CollectionResultT, ElementResultT],
):
    """Base for set values — like collections.abc.Set.

    Subclasses must override:
        _wrap_set_result(operand): Wrap set operation result.

    Type Parameters:
        CollectionT: Native Python collection type (set[int], frozenset[str])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (union, intersection, ...)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    def _wrap_set_result(self, operand: Term) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> CollectionResultT:
        """Set union."""
        from ..morphisms.abc_set import UnionOp

        return cast("CollectionResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> CollectionResultT:
        """Set intersection."""
        from ..morphisms.abc_set import IntersectionOp

        return cast("CollectionResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> CollectionResultT:
        """Set difference."""
        from ..morphisms.abc_set import DifferenceOp

        return cast("CollectionResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(
        self, other: set[ElementT] | frozenset[ElementT] | Term
    ) -> CollectionResultT:
        """Set symmetric difference."""
        from ..morphisms.abc_set import SymmetricDifferenceOp

        return cast("CollectionResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue:
        """Check if subset."""
        from ..morphisms.abc_set import IsSubsetOp
        from ..values import BoolValue

        return BoolValue(IsSubsetOp(self, other))

    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue:
        """Check if superset."""
        from ..morphisms.abc_set import IsSupersetOp
        from ..values import BoolValue

        return BoolValue(IsSupersetOp(self, other))

    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolValue:
        """Check if disjoint."""
        from ..morphisms.abc_set import IsDisjointOp
        from ..values import BoolValue

        return BoolValue(IsDisjointOp(self, other))


class MutableSetBase[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SetLikeBase[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable set values — like collections.abc.MutableSet.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (add, remove, discard)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    def add(self, value: ElementT) -> CollectionResultT:
        """Add element to set."""
        from ..morphisms.abc_set import AddCmd

        return cast("CollectionResultT", self._wrap_set_result(AddCmd(self, value)))

    def remove(self, value: ElementT) -> CollectionResultT:
        """Remove element from set. Returns INVALID if not found."""
        from ..morphisms.abc_set import RemoveCmd

        return cast("CollectionResultT", self._wrap_set_result(RemoveCmd(self, value)))

    def discard(self, value: ElementT) -> CollectionResultT:
        """Remove element if present (no error if absent)."""
        from ..morphisms.abc_set import DiscardCmd

        return cast("CollectionResultT", self._wrap_set_result(DiscardCmd(self, value)))
