"""Set collection: bases + mutations.

SetLikeForm = Collection + union/intersection/difference/symmetric_difference/issubset/issuperset/isdisjoint
    + copy + __or__/__and__/__sub__/__xor__
MutableSetForm = SetLike + add/remove/discard/pop/clear/update/*_update + __ior__/__iand__/__isub__/__ixor__

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

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from .collection import CollectionForm


if TYPE_CHECKING:
    from nu.forms.primitives import Bool
    from nu.lang import Arg, Nu


__all__ = [
    "MutableSetForm",
    "ReactiveSetForm",
    "SetLikeForm",
]


CollectionT = TypeVar("CollectionT")
ElementT = TypeVar("ElementT")
CollectionResultT = TypeVar("CollectionResultT")
ElementResultT = TypeVar("ElementResultT")


class SetLikeForm(
    CollectionForm[ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for set values, like collections.abc.Set.

    Ops: union, intersection, difference, symmetric_difference, issubset,
    issuperset, isdisjoint, copy, and operators | & - ^.

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
        """Union with ``other``."""
        from .set_interactions import Union

        return cast("CollectionResultT", self._wrap_set_result(Union(self, other)))

    def intersection(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Intersection with ``other``."""
        from .set_interactions import Intersection

        return cast("CollectionResultT", self._wrap_set_result(Intersection(self, other)))

    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Difference with ``other``."""
        from .set_interactions import Difference

        return cast("CollectionResultT", self._wrap_set_result(Difference(self, other)))

    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT:
        """Symmetric difference with ``other``."""
        from .set_interactions import SymmetricDifference

        return cast("CollectionResultT", self._wrap_set_result(SymmetricDifference(self, other)))

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """True if every element is in ``other``."""
        from nu.forms.primitives import Bool

        from .set_interactions import IsSubset

        return Bool(IsSubset(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """True if every element of ``other`` is in this set."""
        from nu.forms.primitives import Bool

        from .set_interactions import IsSuperset

        return Bool(IsSuperset(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """True if no elements are shared with ``other``."""
        from nu.forms.primitives import Bool

        from .set_interactions import IsDisjoint

        return Bool(IsDisjoint(self, other))

    def copy(self) -> CollectionResultT:
        """Shallow copy. Returns a new set."""
        from .set_interactions import Copy

        return cast("CollectionResultT", self._wrap_set_result(Copy(self)))

    def __or__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        from .set_interactions import SetOr

        return cast("CollectionResultT", self._wrap_set_result(SetOr(self, other)))

    def __and__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        from .set_interactions import SetAnd

        return cast("CollectionResultT", self._wrap_set_result(SetAnd(self, other)))

    def __sub__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        from .set_interactions import SetSub

        return cast("CollectionResultT", self._wrap_set_result(SetSub(self, other)))

    def __xor__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        from .set_interactions import SetXor

        return cast("CollectionResultT", self._wrap_set_result(SetXor(self, other)))


class MutableSetForm(
    SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable set values, like collections.abc.MutableSet.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (add, remove, discard)
        ElementResultT: Result for element-level interactions (sum_, min_, max_)
    """

    def add(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Add element to set. Mutates the set; returns nothing."""
        from .set_interactions import AddCmd

        return AddCmd(self, value)

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element from set. Mutates the set; returns nothing (KeyError if absent)."""
        from .set_interactions import Remove

        return Remove(self, value)

    def discard(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove element if present (no error if absent). Mutates the set; returns nothing."""
        from .set_interactions import Discard

        return Discard(self, value)

    def pop(self) -> ElementResultT:
        """Remove and return arbitrary element. Mutates the set; returns the element."""
        from .set_interactions import SetPop

        return cast("ElementResultT", self._wrap_element_result(SetPop(self)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items. Mutates the set; returns nothing."""
        from .shared_interactions import Clear

        return Clear(self)

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Add all elements from other. Mutates the set; returns nothing."""
        from .set_interactions import SetUpdate

        return SetUpdate(self, other)

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep only elements found in both. Mutates the set; returns nothing."""
        from .set_interactions import IntersectionUpdate

        return IntersectionUpdate(self, other)

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Remove all elements found in other. Mutates the set; returns nothing."""
        from .set_interactions import DifferenceUpdate

        return DifferenceUpdate(self, other)

    def symmetric_difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep elements in either set but not both. Mutates the set; returns nothing."""
        from .set_interactions import SymmetricDifferenceUpdate

        return SymmetricDifferenceUpdate(self, other)

    def __ior__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place union: self |= other. Mutates the set; returns the set."""
        from .set_interactions import SetIOr

        return cast("CollectionResultT", self._wrap_set_result(SetIOr(self, other)))

    def __iand__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place intersection: self &= other. Mutates the set; returns the set."""
        from .set_interactions import SetIAnd

        return cast("CollectionResultT", self._wrap_set_result(SetIAnd(self, other)))

    def __isub__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place difference: self -= other. Mutates the set; returns the set."""
        from .set_interactions import SetISub

        return cast("CollectionResultT", self._wrap_set_result(SetISub(self, other)))

    def __ixor__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """In-place symmetric difference: self ^= other. Mutates the set; returns the set."""
        from .set_interactions import SetIXor

        return cast("CollectionResultT", self._wrap_set_result(SetIXor(self, other)))


class ReactiveSetForm(
    MutableSetForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Reactive set. Adds on_change() for any-change observation.

    Provides (in addition to MutableSetForm):
        on_change() → OnChange

    The three tree-aware methods (on_child_change, on_children_change,
    on_descendants_change) are shape-domain and live on
    ``nu.domains.shape.forms.collection.ReactiveCollectionForm``.
    """

    def on_change(self) -> object:
        """Subscribe to any change on this set slot."""
        from nu.core.reactive import OnChange

        return OnChange(self)
