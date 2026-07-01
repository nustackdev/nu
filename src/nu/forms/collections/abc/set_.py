"""SetQuery collection — bases + mutations.

SetLikeForm = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
    + copy + __or__/__and__/__sub__/__xor__
MutableSetForm = SetLike + add/remove/discard/pop/clear/update/*_update + __ior__/__iand__/__isub__/__ixor__

Follows Python's collections.abc.SetQuery / MutableSet pattern.

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
    from nu.forms.primitives import BoolForm
    from nu.lang import Arg, Nu


__all__ = [
    "MutableSetForm",
    "ReactiveSetForm",
    "SetLikeForm",
]


class SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionForm[ElementT, CollectionResultT, ElementResultT],
):
    """Base for set values — like collections.abc.SetQuery.

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
        """SetQuery union."""
        from .set_interactions import UnionQuery

        return cast("CollectionResultT", self._wrap_set_result(UnionQuery(self, other)))

    def intersection(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """SetQuery intersection."""
        from .set_interactions import IntersectionQuery

        return cast("CollectionResultT", self._wrap_set_result(IntersectionQuery(self, other)))

    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """SetQuery difference."""
        from .set_interactions import DifferenceQuery

        return cast("CollectionResultT", self._wrap_set_result(DifferenceQuery(self, other)))

    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT:
        """SetQuery symmetric difference."""
        from .set_interactions import SymmetricDifferenceQuery

        return cast(
            "CollectionResultT", self._wrap_set_result(SymmetricDifferenceQuery(self, other))
        )

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if subset."""
        from nu.forms.primitives import BoolForm

        from .set_interactions import IsSubsetQuery

        return BoolForm(IsSubsetQuery(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if superset."""
        from nu.forms.primitives import BoolForm

        from .set_interactions import IsSupersetQuery

        return BoolForm(IsSupersetQuery(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> BoolForm:
        """Check if disjoint."""
        from nu.forms.primitives import BoolForm

        from .set_interactions import IsDisjointQuery

        return BoolForm(IsDisjointQuery(self, other))

    def copy(self) -> CollectionResultT:
        """Shallow copy. Returns a new set."""
        from .set_interactions import CopyQuery

        return cast("CollectionResultT", self._wrap_set_result(CopyQuery(self)))

    def __or__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """SetQuery union operator: self | other. Returns a new set."""
        from .set_interactions import SetOrQuery

        return cast("CollectionResultT", self._wrap_set_result(SetOrQuery(self, other)))

    def __and__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """SetQuery intersection operator: self & other. Returns a new set."""
        from .set_interactions import SetAndQuery

        return cast("CollectionResultT", self._wrap_set_result(SetAndQuery(self, other)))

    def __sub__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """SetQuery difference operator: self - other. Returns a new set."""
        from .set_interactions import SetSubQuery

        return cast("CollectionResultT", self._wrap_set_result(SetSubQuery(self, other)))

    def __xor__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """SetQuery symmetric difference operator: self ^ other. Returns a new set."""
        from .set_interactions import SetXorQuery

        return cast("CollectionResultT", self._wrap_set_result(SetXorQuery(self, other)))


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
        """AddQuery element to set. Mutates the set; returns nothing."""
        from .set_interactions import AddCommand

        return AddCommand(self, value)

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element from set. Mutates the set; returns nothing (KeyError if absent)."""
        from .set_interactions import RemoveCommand

        return RemoveCommand(self, value)

    def discard(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element if present (no error if absent). Mutates the set; returns nothing."""
        from .set_interactions import DiscardCommand

        return DiscardCommand(self, value)

    def pop(self) -> ElementResultT:
        """Remove and return arbitrary element. Mutates the set; returns the element."""
        from .set_interactions import SetPopAction

        return cast("ElementResultT", self._wrap_element_result(SetPopAction(self)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items. Mutates the set; returns nothing."""
        from .shared_interactions import ClearCommand

        return ClearCommand(self)

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """AddQuery all elements from other. Mutates the set; returns nothing."""
        from .set_interactions import SetUpdateCommand

        return SetUpdateCommand(self, other)

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep only elements found in both. Mutates the set; returns nothing."""
        from .set_interactions import IntersectionUpdateCommand

        return IntersectionUpdateCommand(self, other)

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Remove all elements found in other. Mutates the set; returns nothing."""
        from .set_interactions import DifferenceUpdateCommand

        return DifferenceUpdateCommand(self, other)

    def symmetric_difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep elements in either set but not both. Mutates the set; returns nothing."""
        from .set_interactions import SymmetricDifferenceUpdateCommand

        return SymmetricDifferenceUpdateCommand(self, other)

    def __ior__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place union: self |= other. Mutates the set; returns the set."""
        from .set_interactions import SetIOrAction

        return cast("CollectionResultT", self._wrap_set_result(SetIOrAction(self, other)))

    def __iand__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place intersection: self &= other. Mutates the set; returns the set."""
        from .set_interactions import SetIAndAction

        return cast("CollectionResultT", self._wrap_set_result(SetIAndAction(self, other)))

    def __isub__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place difference: self -= other. Mutates the set; returns the set."""
        from .set_interactions import SetISubAction

        return cast("CollectionResultT", self._wrap_set_result(SetISubAction(self, other)))

    def __ixor__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place symmetric difference: self ^= other. Mutates the set; returns the set."""
        from .set_interactions import SetIXorAction

        return cast("CollectionResultT", self._wrap_set_result(SetIXorAction(self, other)))


class ReactiveSetForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    MutableSetForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Reactive set — adds on_change() for any-change observation.

    Provides (in addition to MutableSetForm):
        on_change() → OnChangeQuery

    The three tree-aware methods (on_child_change, on_children_change,
    on_descendants_change) are shape-domain and live on
    ``nu.domains.shape.forms.collection.ReactiveCollectionForm``.
    """

    def on_change(self) -> object:
        """Subscribe to any change on this set slot."""
        from nu.core.reactive import OnChangeQuery

        return OnChangeQuery(self)
