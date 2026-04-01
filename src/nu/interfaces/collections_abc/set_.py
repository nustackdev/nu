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

from .collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from nu.terms import Arg, Nu

    from ..values import BoolValue, NoneValue


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

    def union(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT: ...
    def intersection(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT: ...
    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT: ...
    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT: ...
    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolValue: ...
    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolValue: ...
    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolValue: ...


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

    def add(self, value: Arg[ElementT]) -> NoneValue: ...
    def remove(self, value: Arg[ElementT]) -> NoneValue: ...
    def discard(self, value: Arg[ElementT]) -> NoneValue: ...
    def pop(self) -> ElementResultT: ...
    def clear(self) -> NoneValue: ...
    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneValue: ...
    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneValue: ...
    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneValue: ...
    def symmetric_difference_update(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> NoneValue: ...


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

    def _wrap_set_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set union."""
        from nu.ops.collections.set import UnionOp

        return cast("CollectionResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set intersection."""
        from nu.ops.collections.set import IntersectionOp

        return cast("CollectionResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set difference."""
        from nu.ops.collections.set import DifferenceOp

        return cast("CollectionResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT:
        """Set symmetric difference."""
        from nu.ops.collections.set import SymmetricDifferenceOp

        return cast("CollectionResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolValue:
        """Check if subset."""
        from nu.ops.collections.set import IsSubsetOp
        from ..values import BoolValue

        return BoolValue(IsSubsetOp(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolValue:
        """Check if superset."""
        from nu.ops.collections.set import IsSupersetOp
        from ..values import BoolValue

        return BoolValue(IsSupersetOp(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolValue:
        """Check if disjoint."""
        from nu.ops.collections.set import IsDisjointOp
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

    def add(self, value: Arg[ElementT]) -> NoneValue:
        """Add element to set."""
        from nu.ops.collections.set import AddCmd
        from ..values import NoneValue

        return NoneValue(AddCmd(self, value))

    def remove(self, value: Arg[ElementT]) -> NoneValue:
        """Remove element from set. Returns INVALID if not found."""
        from nu.ops.collections.set import RemoveCmd
        from ..values import NoneValue

        return NoneValue(RemoveCmd(self, value))

    def discard(self, value: Arg[ElementT]) -> NoneValue:
        """Remove element if present (no error if absent)."""
        from nu.ops.collections.set import DiscardCmd
        from ..values import NoneValue

        return NoneValue(DiscardCmd(self, value))

    def pop(self) -> ElementResultT:
        """Remove and return arbitrary element."""
        from nu.ops.collections.set import SetPopCmd

        return cast("ElementResultT", self._wrap_element_result(SetPopCmd(self)))

    def clear(self) -> NoneValue:
        """Remove all items."""
        from nu.ops.collections.shared import ClearCmd
        from ..values import NoneValue

        return NoneValue(ClearCmd(self))

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneValue:
        """Add all elements from other."""
        from nu.ops.collections.set import SetUpdateCmd
        from ..values import NoneValue

        return NoneValue(SetUpdateCmd(self, other))

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneValue:
        """Keep only elements found in both."""
        from nu.ops.collections.set import IntersectionUpdateCmd
        from ..values import NoneValue

        return NoneValue(IntersectionUpdateCmd(self, other))

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> NoneValue:
        """Remove all elements found in other."""
        from nu.ops.collections.set import DifferenceUpdateCmd
        from ..values import NoneValue

        return NoneValue(DifferenceUpdateCmd(self, other))

    def symmetric_difference_update(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> NoneValue:
        """Keep elements in either set but not both."""
        from nu.ops.collections.set import SymmetricDifferenceUpdateCmd
        from ..values import NoneValue

        return NoneValue(SymmetricDifferenceUpdateCmd(self, other))
