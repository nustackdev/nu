"""Set collection — bases + mutations.

SetLikeForm = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
MutableSetForm = SetLike + add/remove/discard

Follows Python's collections.abc.Set / MutableSet pattern.

Type Parameters:
    CollectionT: Native Python collection type (set[int], frozenset[str], etc.)
    ElementT: Native Python element type (int, str, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
        (union, intersection, difference, symmetric_difference, add, remove, discard)
    ElementResultT: Wrapped result for element-level interactions
        (sum_, min_, max_)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .collection import CollectionForm


if TYPE_CHECKING:
    from nu2.forms.primitives import BoolForm
    from nu2.lang import Arg, Nu


__all__ = [
    "MutableSetForm",
    "SetLikeForm",
]


class SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionForm[ElementT, CollectionResultT, ElementResultT],
):
    """Base for set values — like collections.abc.Set.

    Subclasses must override:
        _wrap_set_result(operand): Wrap set interaction result.

    Type Parameters:
        CollectionT: Native Python collection type (set[int], frozenset[str])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (union, intersection, ...)
        ElementResultT: Result for element-level interactions (sum_, min_, max_)
    """

    def _wrap_set_result(self, operand: Nu) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set union."""
        from .set_interactions import UnionQuery

        return cast("CollectionResultT", self._wrap_set_result(UnionQuery(self, other)))

    def intersection(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set intersection."""
        from .set_interactions import IntersectionQuery

        return cast("CollectionResultT", self._wrap_set_result(IntersectionQuery(self, other)))

    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Set difference."""
        from .set_interactions import DifferenceQuery

        return cast("CollectionResultT", self._wrap_set_result(DifferenceQuery(self, other)))

    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT:
        """Set symmetric difference."""
        from .set_interactions import SymmetricDifferenceQuery

        return cast(
            "CollectionResultT", self._wrap_set_result(SymmetricDifferenceQuery(self, other))
        )

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if subset."""
        from nu2.forms.primitives import BoolForm

        from .set_interactions import IsSubsetQuery

        return BoolForm(IsSubsetQuery(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if superset."""
        from nu2.forms.primitives import BoolForm

        from .set_interactions import IsSupersetQuery

        return BoolForm(IsSupersetQuery(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if disjoint."""
        from nu2.forms.primitives import BoolForm

        from .set_interactions import IsDisjointQuery

        return BoolForm(IsDisjointQuery(self, other))


class MutableSetForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable set values — like collections.abc.MutableSet.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (add, remove, discard)
        ElementResultT: Result for element-level interactions (sum_, min_, max_)
    """

    def add(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Add element to set."""
        from .set_interactions import AddQuery

        return AddQuery(self, value)

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element from set. Returns INVALID if not found."""
        from .set_interactions import RemoveQuery

        return RemoveQuery(self, value)

    def discard(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element if present (no error if absent)."""
        from .set_interactions import DiscardQuery

        return DiscardQuery(self, value)

    def pop(self) -> ElementResultT:
        """Remove and return arbitrary element."""
        from .set_interactions import SetPopQuery

        return cast("ElementResultT", self._wrap_element_result(SetPopQuery(self)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items."""
        from .shared_interactions import ClearQuery

        return ClearQuery(self)

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Add all elements from other."""
        from .set_interactions import SetUpdateQuery

        return SetUpdateQuery(self, other)

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep only elements found in both."""
        from .set_interactions import IntersectionUpdateQuery

        return IntersectionUpdateQuery(self, other)

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Remove all elements found in other."""
        from .set_interactions import DifferenceUpdateQuery

        return DifferenceUpdateQuery(self, other)

    def symmetric_difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep elements in either set but not both."""
        from .set_interactions import SymmetricDifferenceUpdateQuery

        return SymmetricDifferenceUpdateQuery(self, other)
