"""Set collection — bases + mutations.

SetLikeForm = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
MutableSetForm = SetLike + add/remove/discard

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

from typing import TYPE_CHECKING, Any, cast

from .collection import CollectionForm


if TYPE_CHECKING:
    from nu.forms.primitives import BoolForm
    from nu.terms import Arg, Nu


__all__ = [
    "MutableSetForm",
    "SetLikeForm",
]


class SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionForm[ElementT, CollectionResultT, ElementResultT],
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

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if subset."""
        from nu.forms.primitives import BoolForm

        from .set_ops import IsSubsetOp

        return BoolForm(IsSubsetOp(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if superset."""
        from nu.forms.primitives import BoolForm

        from .set_ops import IsSupersetOp

        return BoolForm(IsSupersetOp(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if disjoint."""
        from nu.forms.primitives import BoolForm

        from .set_ops import IsDisjointOp

        return BoolForm(IsDisjointOp(self, other))


class MutableSetForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable set values — like collections.abc.MutableSet.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (add, remove, discard)
        ElementResultT: Result for element-level ops (sum_, min_, max_)
    """

    def add(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Add element to set."""
        from .set_ops import AddCmd

        return AddCmd(self, value)

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element from set. Returns INVALID if not found."""
        from .set_ops import RemoveCmd

        return RemoveCmd(self, value)

    def discard(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element if present (no error if absent)."""
        from .set_ops import DiscardCmd

        return DiscardCmd(self, value)

    def pop(self) -> ElementResultT:
        """Remove and return arbitrary element."""
        from .set_ops import SetPopCmd

        return cast("ElementResultT", self._wrap_element_result(SetPopCmd(self)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items."""
        from .shared_ops import ClearCmd

        return ClearCmd(self)

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Add all elements from other."""
        from .set_ops import SetUpdateCmd

        return SetUpdateCmd(self, other)

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep only elements found in both."""
        from .set_ops import IntersectionUpdateCmd

        return IntersectionUpdateCmd(self, other)

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Remove all elements found in other."""
        from .set_ops import DifferenceUpdateCmd

        return DifferenceUpdateCmd(self, other)

    def symmetric_difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep elements in either set but not both."""
        from .set_ops import SymmetricDifferenceUpdateCmd

        return SymmetricDifferenceUpdateCmd(self, other)
