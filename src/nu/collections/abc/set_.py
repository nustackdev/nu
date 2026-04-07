# ruff: noqa: D102
"""Set collection — bases + mutations.

SetLikeI = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
MutableSetI = SetLike + add/remove/discard

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

from typing import TYPE_CHECKING, cast

from .collection import CollectionI


if TYPE_CHECKING:
    from nu.primitives import BoolI, NoneI
    from nu.terms import Arg, Nu


__all__ = [
    "MutableSetI",
    "SetLikeI",
]


class SetLikeI[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionI[ElementT, CollectionResultT, ElementResultT],
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

    def _wrap_set_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set union."""
        from .set_ops import UnionOp

        return cast("CollectionResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set intersection."""
        from .set_ops import IntersectionOp

        return cast("CollectionResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set difference."""
        from .set_ops import DifferenceOp

        return cast("CollectionResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT:
        """Set symmetric difference."""
        from .set_ops import SymmetricDifferenceOp

        return cast("CollectionResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolI:
        """Check if subset."""
        from nu.primitives import BoolI

        from .set_ops import IsSubsetOp

        return BoolI(IsSubsetOp(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolI:
        """Check if superset."""
        from nu.primitives import BoolI

        from .set_ops import IsSupersetOp

        return BoolI(IsSupersetOp(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolI:
        """Check if disjoint."""
        from nu.primitives import BoolI

        from .set_ops import IsDisjointOp

        return BoolI(IsDisjointOp(self, other))


class MutableSetI[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SetLikeI[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable set values — like collections.abc.MutableSet.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (add, remove, discard)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    def add(self, value: Arg[ElementT]) -> NoneI:
        """Add element to set."""
        from nu.primitives import NoneI

        from .set_ops import AddCmd

        return NoneI(AddCmd(self, value))

    def remove(self, value: Arg[ElementT]) -> NoneI:
        """Remove element from set. Returns INVALID if not found."""
        from nu.primitives import NoneI

        from .set_ops import RemoveCmd

        return NoneI(RemoveCmd(self, value))

    def discard(self, value: Arg[ElementT]) -> NoneI:
        """Remove element if present (no error if absent)."""
        from nu.primitives import NoneI

        from .set_ops import DiscardCmd

        return NoneI(DiscardCmd(self, value))

    def pop(self) -> ElementResultT:
        """Remove and return arbitrary element."""
        from .set_ops import SetPopCmd

        return cast("ElementResultT", self._wrap_element_result(SetPopCmd(self)))

    def clear(self) -> NoneI:
        """Remove all items."""
        from nu.primitives import NoneI

        from .shared_ops import ClearCmd

        return NoneI(ClearCmd(self))

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneI:
        """Add all elements from other."""
        from nu.primitives import NoneI

        from .set_ops import SetUpdateCmd

        return NoneI(SetUpdateCmd(self, other))

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneI:
        """Keep only elements found in both."""
        from nu.primitives import NoneI

        from .set_ops import IntersectionUpdateCmd

        return NoneI(IntersectionUpdateCmd(self, other))

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneI:
        """Remove all elements found in other."""
        from nu.primitives import NoneI

        from .set_ops import DifferenceUpdateCmd

        return NoneI(DifferenceUpdateCmd(self, other))

    def symmetric_difference_update(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> NoneI:
        """Keep elements in either set but not both."""
        from nu.primitives import NoneI

        from .set_ops import SymmetricDifferenceUpdateCmd

        return NoneI(SymmetricDifferenceUpdateCmd(self, other))
