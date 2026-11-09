"""Set collection: bases + mutations.

SetLikeForm = Collection + subset comparisons (< <= > >=) + isdisjoint
    + union/intersection/difference/symmetric_difference/issubset/issuperset
MutableSetForm = SetLike + add/remove/discard/pop/clear
    + update/intersection_update/difference_update/symmetric_difference_update

Follows Python's collections.abc.Set / MutableSet pattern. Nu reserves ``&``
and ``|`` (they compose flows on every term) and leaves ``-`` / ``^`` undefined,
so the ABC's set operators are spelled with Python's named methods: ``union``
for ``|``, ``intersection`` for ``&``, ``difference`` for ``-``,
``symmetric_difference`` for ``^``, ``issubset`` / ``issuperset`` beside
``<=`` / ``>=``, and the ``*update`` methods for ``|= &= -= ^=``. ``copy`` is
built-in only and lives on ``Set`` / ``FrozenSet``.

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

    Ops: the subset comparisons (`<`, `<=`, `>`, `>=`), isdisjoint, and
    union, intersection, difference, symmetric_difference, issubset,
    issuperset.

    Notes:
        - The named methods are Nu's spelling of the Set ABC operators:
          `&`, `|` and `>>` compose flows on a set like on every term, and
          `-` / `^` are not defined.
        - `copy` is built-in only and lives on `Set` / `FrozenSet`.
        - Subclasses (e.g. `Set`) must implement `_wrap_set_result` to wrap
          a query result in their own concrete set type.
        - Every op accepts a plain Python `set`/`frozenset` or another
          set-like form as the right operand.

    Type Parameters:
        CollectionT: Native Python collection type (set[int], frozenset[str])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (union, intersection, ...)
        ElementResultT: Result for element-level interactions (sum_, min_, max_)

    Example:
        >>> nu.run(nu.Set({1, 2}).union({2, 3}))[0]
        {1, 2, 3}
    """

    def _wrap_set_result(self, operand: Nu) -> CollectionResultT:
        """Wrap a set-level interaction result in the concrete set type.

        Notes:
            - Abstract hook. Subclasses (e.g. `Set`) implement this so
              `union`/`intersection`/etc. know what to wrap into; not
              meant to be called directly.

        Yields:
            Raises NotImplementedError when left unoverridden.
        """
        raise NotImplementedError()

    def union(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Union of self and other.

        Args:
            other: the set to union with self.

        Yields:
            A new set with every element from self and other.

        Example:
            >>> nu.run(nu.Set({1, 2}).union({2, 3}))[0]
            {1, 2, 3}
        """
        from .set_interactions import Union

        return cast("CollectionResultT", self._wrap_set_result(Union(self, other)))

    def intersection(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Intersection of self and other.

        Args:
            other: the set to intersect with self.

        Yields:
            A new set with only the elements found in both.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).intersection({2, 3, 4}))[0]
            {2, 3}
        """
        from .set_interactions import Intersection

        return cast("CollectionResultT", self._wrap_set_result(Intersection(self, other)))

    def difference(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> CollectionResultT:
        """Elements of self that are not in other.

        Args:
            other: the set to subtract from self.

        Yields:
            A new set with the elements of self minus the elements of
            other.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).difference({2, 3}))[0]
            {1}
        """
        from .set_interactions import Difference

        return cast("CollectionResultT", self._wrap_set_result(Difference(self, other)))

    def symmetric_difference(
        self, other: Arg[set[ElementT] | frozenset[ElementT]]
    ) -> CollectionResultT:
        """Elements in exactly one of self and other, not both.

        Args:
            other: the set to compare against self.

        Yields:
            A new set with the elements that are in self or other but not
            in both.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).symmetric_difference({2, 3, 4}))[0]
            {1, 4}
        """
        from .set_interactions import SymmetricDifference

        return cast("CollectionResultT", self._wrap_set_result(SymmetricDifference(self, other)))

    def issubset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Whether every element of self is in other.

        Args:
            other: the set to test self against.

        Yields:
            True when self is a subset of other (equal sets count), False
            otherwise.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).issubset({1, 2, 3, 4}))[0]
            True
        """
        from nu.forms.primitives import Bool

        from .set_interactions import IsSubset

        return Bool(IsSubset(self, other))

    def issuperset(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Whether every element of other is in self.

        Args:
            other: the set to test against self.

        Yields:
            True when self is a superset of other (equal sets count),
            False otherwise.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).issuperset({1, 2}))[0]
            True
        """
        from nu.forms.primitives import Bool

        from .set_interactions import IsSuperset

        return Bool(IsSuperset(self, other))

    def __gt__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Self is a proper superset of other.

        Args:
            other: the set to compare against.

        Yields:
            True when self contains every element of other and at least one
            more, False otherwise.

        Example:
            >>> nu.run(nu.Set.of(1, 2, 3) > nu.Set.of(1, 2))[0]
            True
        """
        from nu.core import Gt
        from nu.forms.primitives import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Self is a proper subset of other.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of self is in other and other has at
            least one more, False otherwise.

        Example:
            >>> nu.run(nu.Set.of(1, 2) < nu.Set.of(1, 2, 3))[0]
            True
        """
        from nu.core import Lt
        from nu.forms.primitives import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Self is a superset of other, or equal.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of other is in self, False otherwise.

        Example:
            >>> nu.run(nu.Set.of(1, 2) >= nu.Set.of(1, 2))[0]
            True
        """
        from nu.core import Ge
        from nu.forms.primitives import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Self is a subset of other, or equal.

        Args:
            other: the set to compare against.

        Yields:
            True when every element of self is in other, False otherwise.

        Example:
            >>> nu.run(nu.Set.of(1, 2) <= nu.Set.of(1, 2))[0]
            True
        """
        from nu.core import Le
        from nu.forms.primitives import Bool

        return Bool(Le(self, other))

    def isdisjoint(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Bool:
        """Whether self and other share no elements.

        Args:
            other: the set to test against self.

        Yields:
            True when self and other have no elements in common, False
            otherwise.

        Example:
            >>> nu.run(nu.Set({1, 2, 3}).isdisjoint({9, 10}))[0]
            True
        """
        from nu.forms.primitives import Bool

        from .set_interactions import IsDisjoint

        return Bool(IsDisjoint(self, other))


class MutableSetForm(
    SetLikeForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable set values, like collections.abc.MutableSet.

    Adds add/remove/discard/pop/clear on top of SetLikeForm, and the
    `update` / `*_update` methods: Nu's spelling of the ABC's in-place
    operators `|= &= -= ^=`, which Nu reserves or leaves undefined.

    Notes:
        - Every mutating method needs self bound to a Ref inside a shape;
          none of them run on a bare set literal.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (add, remove, discard)
        ElementResultT: Result for element-level interactions (sum_, min_, max_)
    """

    def add(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Add value to self.

        Args:
            value: the element to add.

        Notes:
            - A no-op if value is already present, matching Python's
              `set.add`.

        Yields:
            Nothing (Command). Mutates self in place.

        Example::

            my_set.add(4)
        """
        from .set_interactions import AddCmd

        return AddCmd(self, value)

    def remove(self, value: Arg[ElementT], *, missing_ok: bool = False) -> Any:  # noqa: ANN401
        """Remove value from self.

        Args:
            value: the element to remove.
            missing_ok: when ``True``, an absent value is a no-op. A plain
                Python bool fixed at construction, not a Nu value.

        Notes:
            - By default raises at evaluation time when value is absent,
              matching Python's `set.remove`.

        Yields:
            Nothing (Command). Mutates self in place.

        Example:
            >>> class Port(nu.Shape):
            ...     members = nu.SetRef.slot(str)
            >>> data = {"members": {"a", "b"}}
            >>> ctx = nu.Context().bind(dict, data, Port)
            >>> _ = nu.run(Port.members.remove("a"), ctx)
            >>> _ = nu.run(Port.members.remove("z", missing_ok=True), ctx)
            >>> data
            {'members': {'b'}}
        """
        from .set_interactions import Remove

        return Remove(self, value, missing_ok=missing_ok)

    def discard(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove value from self if present.

        Args:
            value: the element to remove.

        Notes:
            - Unlike `remove`, a missing value is not an error.

        Yields:
            Nothing (Command). Mutates self in place.

        Example::

            my_set.discard(4)
        """
        from .set_interactions import Discard

        return Discard(self, value)

    def pop(self) -> ElementResultT:
        """Remove and return an arbitrary element from self.

        Notes:
            - Which element comes out is unspecified; do not rely on an
              order.
            - Raises at evaluation time when self is empty.

        Yields:
            The removed element. Mutates self in place. Raises at
            evaluation time when self is empty.

        Example::

            my_set.pop()
        """
        from .set_interactions import SetPop

        return cast("ElementResultT", self._wrap_element_result(SetPop(self)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove every element from self.

        Yields:
            Nothing (Command). Mutates self in place, leaving it empty.

        Example::

            my_set.clear()
        """
        from .shared_interactions import Clear

        return Clear(self)

    def update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Add every element of other to self.

        Args:
            other: the set whose elements are added to self.

        Yields:
            Nothing (Command). Mutates self in place.

        Example::

            my_set.update({4, 5})
        """
        from .set_interactions import SetUpdate

        return SetUpdate(self, other)

    def intersection_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep only the elements of self also found in other.

        Args:
            other: the set to intersect self with.

        Yields:
            Nothing (Command). Mutates self in place.

        Example::

            my_set.intersection_update({2, 3})
        """
        from .set_interactions import IntersectionUpdate

        return IntersectionUpdate(self, other)

    def difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Remove every element of other from self.

        Args:
            other: the set of elements to remove from self.

        Yields:
            Nothing (Command). Mutates self in place.

        Example::

            my_set.difference_update({2, 3})
        """
        from .set_interactions import DifferenceUpdate

        return DifferenceUpdate(self, other)

    def symmetric_difference_update(self, other: Arg[set[ElementT] | frozenset[ElementT]]) -> Any:  # noqa: ANN401
        """Keep the elements in exactly one of self and other.

        Args:
            other: the set to compare self against.

        Yields:
            Nothing (Command). Mutates self in place.

        Example::

            my_set.symmetric_difference_update({2, 4})
        """
        from .set_interactions import SymmetricDifferenceUpdate

        return SymmetricDifferenceUpdate(self, other)


class ReactiveSetForm(
    MutableSetForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Reactive set. Adds on_change() for any-change observation.

    Notes:
        - The three tree-aware methods (on_child_change,
          on_children_change, on_descendants_change) are shape-domain and
          live on `nu.domains.shape.collection.ReactiveCollectionForm`,
          not here.

    Example::

        my_set.on_change()
    """

    def on_change(self) -> object:
        """Subscribe to any change on this set slot.

        Yields:
            An OnChange observable that fires whenever self changes.

        Example::

            my_set.on_change()
        """
        from nu.core.reactive import OnChange

        return OnChange(self)
