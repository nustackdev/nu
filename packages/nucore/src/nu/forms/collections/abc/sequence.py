"""Sequence collection: bases + mutations.

SequenceForm = Collection + Sliceable + first/last/index/count/reversed
MutableSequenceForm = Sequence + append/insert/pop/extend/remove/reverse

Sorted/Reversed are standalone functions in ``abc.fn``.

Follows Python's collections.abc.Sequence / MutableSequence pattern.

Type Parameters:
    CollectionT: Native Python collection type (list[int], tuple[str, ...], etc.)
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level interactions
        (slice_, append, insert, extend, remove)
    ElementResultT: Wrapped result for element-level interactions
        (first, last, pop)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast, overload

from .collection import CollectionForm
from .sliceable import SliceableForm


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.forms.primitives import Int
    from nu.lang import Arg, IntArg


__all__ = [
    "MutableSequenceForm",
    "ReactiveSequenceForm",
    "SequenceForm",
]


CollectionT = TypeVar("CollectionT")
ElementT = TypeVar("ElementT")
CollectionResultT = TypeVar("CollectionResultT")
ElementResultT = TypeVar("ElementResultT")


class SequenceForm(
    CollectionForm[ElementT, CollectionResultT, ElementResultT],
    SliceableForm[CollectionResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for ordered, indexable values, like collections.abc.Sequence.

    Notes:
        - Mixed in by List, Str, Bytes, Tuple, ListRef; this class only
          carries the shared shape. Concrete carriers narrow
          CollectionResultT/ElementResultT to their own types.
        - Order is positional and stable: iteration, indexing, and
          `first_elem`/`last_elem` all agree on the same order.

    Type Parameters:
        CollectionT: Native Python collection type (list[int], tuple[str, ...])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (map_, filter_, reversed_, sorted_)
        ElementResultT: Result for element-level interactions (first, last, sum_, min_, max_)
    """

    @overload
    def __getitem__(self, key: IntArg) -> ElementResultT: ...
    @overload
    def __getitem__(self, key: slice) -> CollectionResultT: ...
    def __getitem__(self, key: IntArg | slice) -> ElementResultT | CollectionResultT:
        """Element at an int index, or subsequence for a slice.

        Args:
            key: an int index, or a Python slice of int start/stop/step.

        Notes:
            - An out-of-range int index raises at evaluation time, matching
              Python. A slice never raises; out-of-range bounds clamp like
              Python slicing, so a slice past the end yields a shorter (or
              empty) result rather than erroring.
            - Negative indices and negative slice bounds work as in Python.

        Yields:
            The element for an int key, the subsequence for a slice. INVALID
            when self is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3)[1])[0]
            2

            >>> nu.run(nu.List.of(1, 2, 3)[1:3])[0]
            [2, 3]
        """
        from nu.core import GetItem as At
        from nu.core import Slice

        if isinstance(key, slice):
            return cast(
                "CollectionResultT",
                self._wrap_sliceable_result(At(self, Slice(key.start, key.stop, key.step))),
            )
        return cast("ElementResultT", self._wrap_element_result(At(self, key)))

    def first_elem(self) -> ElementResultT:
        """First element of self.

        Yields:
            The first element. INVALID when self is empty or a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).first_elem())[0]
            1

            >>> nu.run(nu.List.of().first_elem())[0]
            <INVALID>
        """
        from .sequence_interactions import First

        return cast("ElementResultT", self._wrap_element_result(First(self)))

    def last_elem(self) -> ElementResultT:
        """Last element of self.

        Yields:
            The last element. INVALID when self is empty or a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).last_elem())[0]
            3
        """
        from .sequence_interactions import Last

        return cast("ElementResultT", self._wrap_element_result(Last(self)))

    def index(self, value: Arg[ElementT]) -> Int:
        """Lowest index in self where value is found, searching from the left.

        Args:
            value: the element to search for.

        Notes:
            - Unlike Python's `list.index`, a missing value does not raise:
              it yields INVALID instead.

        Yields:
            The lowest matching index. INVALID when self is a sentinel or
            value is not found.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).index(2))[0]
            1

            >>> nu.run(nu.List.of(1, 2, 3).index(5))[0]
            <INVALID>
        """
        from nu.forms.primitives import Int

        from .sequence_interactions import IndexOf

        return Int(IndexOf(self, value))

    def count(self, value: Arg[ElementT]) -> Int:
        """Count of occurrences of value in self.

        Args:
            value: the element to count.

        Yields:
            The occurrence count, `0` when value is absent. INVALID when
            self is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2, 2, 3).count(2))[0]
            2
        """
        from nu.forms.primitives import Int

        from .sequence_interactions import Count

        return Int(Count(self, value))

    def reversed(self) -> CollectionResultT:
        """Self walked back to front, as a stream.

        Notes:
            - Yields a stream, not a materialized copy; consume it through
              a Flow (`ForEachDo`) or a Ref-backed context. It doesn't
              evaluate standalone as a scalar against a plain sequence
              value.

        Yields:
            The elements of self in reverse order.
        """
        from nu.core import Reversed

        return cast("CollectionResultT", self._wrap_iterable_result(Reversed(self)))


class MutableSequenceForm(
    SequenceForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for in-place-mutable sequences, like collections.abc.MutableSequence.

    Notes:
        - Every mutator here needs a Ref on the left; none of them evaluate
          standalone against a plain sequence value.
        - `pop` is the one Action (mutates and returns a value); the rest
          are Commands (mutate, yield nothing).

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (append, extend, insert, remove)
        ElementResultT: Result for element-level interactions (pop)
    """

    def append(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Append value to the end of self.

        Args:
            value: the element to append.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import Append

        return Append(self, value)

    def extend(self, other: Arg[Iterable[ElementT]]) -> Any:  # noqa: ANN401
        """Extend self with the elements of other, in order.

        Args:
            other: the iterable of elements to append.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import Extend

        return Extend(self, other)

    def insert(self, index: IntArg, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Insert value at index, shifting later elements right.

        Args:
            index: the position to insert at. Out-of-range indices clamp
                like Python's `list.insert` rather than raising.
            value: the element to insert.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import Insert

        return Insert(self, index, value)

    def pop(self, index: IntArg = -1) -> ElementResultT:
        """Remove and return the element at index.

        Args:
            index: the position to remove. Defaults to the last element.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            The removed element (Action). INVALID when index is out of
            range or self is a sentinel.
        """
        from .sequence_interactions import Pop

        return cast("ElementResultT", self._wrap_element_result(Pop(self, index)))

    def del_at(self, index: IntArg) -> Any:  # noqa: ANN401
        """Remove the element at index.

        Args:
            index: the position to remove. An out-of-range index raises at
                evaluation time, matching Python's `del seq[i]`.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.
            - Use this over `pop` when a Command is wanted instead of the
              Action `pop` yields.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import DelIndex

        return DelIndex(self, index)

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove the first occurrence of value.

        Args:
            value: the element to remove.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.
            - A value that isn't present raises at evaluation time,
              matching Python's `list.remove`.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import RemoveValue

        return RemoveValue(self, value)

    def reverse(self) -> Any:  # noqa: ANN401
        """Reverse self in place.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import Reverse

        return Reverse(self)

    def sort(self) -> Any:  # noqa: ANN401
        """Sort self in place, ascending, using the elements' natural order.

        Notes:
            - No `key` support yet; sorting by a derived key is deferred.
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            Nothing (Command).
        """
        from .sequence_interactions import Sort

        return Sort(self)

    def copy(self) -> CollectionResultT:
        """Shallow copy of self: a new sequence with the same elements.

        Notes:
            - Unlike the mutators above, this is a Query: it doesn't mutate
              self and evaluates fine against a plain sequence value.

        Yields:
            The copy. INVALID when self is a sentinel.

        Example:
            >>> nu.run(nu.List.of(1, 2, 3).copy())[0]
            [1, 2, 3]
        """
        from .sequence_interactions import Copy

        return cast("CollectionResultT", self._wrap_sliceable_result(Copy(self)))

    def clear(self) -> Any:  # noqa: ANN401
        """Remove every element from self.

        Notes:
            - Mutates self and needs a Ref on the left; it can't run
              standalone against a plain sequence value.

        Yields:
            Nothing (Command).
        """
        from .shared_interactions import Clear

        return Clear(self)


class ReactiveSequenceForm(
    MutableSequenceForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Generic[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Sequence with change subscriptions layered on MutableSequenceForm.

    Notes:
        - Adds `on_change` for any-change observation on this slot. The
          three tree-aware variants (on_child_change, on_children_change,
          on_descendants_change) are shape-domain and live on
          `nu.domains.shape.forms.collection.ReactiveCollectionForm`, not
          here.
    """

    def on_change(self) -> object:
        """Subscribe to any change on this sequence slot.

        Yields:
            An event stream firing whenever this slot changes.
        """
        from nu.core.reactive import OnChange

        return OnChange(self)
