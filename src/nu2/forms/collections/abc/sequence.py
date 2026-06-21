"""Sequence collection — bases + mutations.

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

from typing import TYPE_CHECKING, Any, cast

from .collection import CollectionForm
from .sliceable import SliceableForm


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu2.forms.primitives import IntForm
    from nu2.lang import Arg, IntArg


__all__ = [
    "MutableSequenceForm",
    "SequenceForm",
]


class SequenceForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionForm[ElementT, CollectionResultT, ElementResultT],
    SliceableForm[CollectionResultT],
):
    """Base for sequence values — like collections.abc.Sequence.

    Type Parameters:
        CollectionT: Native Python collection type (list[int], tuple[str, ...])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (map_, filter_, reversed_, sorted_)
        ElementResultT: Result for element-level interactions (first, last, sum_, min_, max_)
    """

    def __getitem__(self, key: IntArg | slice) -> ElementResultT | CollectionResultT:
        """Index → element via At; slice → subsequence via Slice."""
        from nu2.core import GetItem as At
        from nu2.core import Slice

        if isinstance(key, slice):
            return cast(
                "CollectionResultT",
                self._wrap_sliceable_result(Slice(self, key.start, key.stop, key.step)),
            )
        return cast("ElementResultT", self._wrap_element_result(At(self, key)))

    def first_elem(self) -> ElementResultT:
        """Get first element."""
        from .sequence_interactions import FirstQuery

        return cast("ElementResultT", self._wrap_element_result(FirstQuery(self)))

    def last_elem(self) -> ElementResultT:
        """Get last element."""
        from .sequence_interactions import LastQuery

        return cast("ElementResultT", self._wrap_element_result(LastQuery(self)))

    def index(self, value: Arg[ElementT]) -> IntForm:
        """Find index of value."""
        from nu2.forms.primitives import IntForm

        from .sequence_interactions import IndexOfQuery

        return IntForm(IndexOfQuery(self, value))

    def count(self, value: Arg[ElementT]) -> IntForm:
        """Count occurrences."""
        from nu2.forms.primitives import IntForm

        from .sequence_interactions import CountQuery

        return IntForm(CountQuery(self, value))

    def reversed(self) -> CollectionResultT:
        """Reversed copy of this sequence."""
        from nu2.core import Reversed

        return cast("CollectionResultT", self._wrap_iterable_result(Reversed(self)))


class MutableSequenceForm[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SequenceForm[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable sequence values — like collections.abc.MutableSequence.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level interactions (append, extend, insert, remove)
        ElementResultT: Result for element-level interactions (pop)
    """

    def append(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Append item to end of sequence."""
        from .sequence_interactions import AppendQuery

        return AppendQuery(self, value)

    def extend(self, other: Arg[Iterable[ElementT]]) -> Any:  # noqa: ANN401
        """Extend sequence with elements from iterable."""
        from .sequence_interactions import ExtendQuery

        return ExtendQuery(self, other)

    def insert(self, index: IntArg, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Insert item at index."""
        from .sequence_interactions import InsertQuery

        return InsertQuery(self, index, value)

    def pop(self, index: IntArg = -1) -> ElementResultT:
        """Remove and return item at index (default: last)."""
        from .sequence_interactions import PopQuery

        return cast("ElementResultT", self._wrap_element_result(PopQuery(self, index)))

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove first occurrence of value."""
        from .sequence_interactions import RemoveValueQuery

        return RemoveValueQuery(self, value)

    def reverse(self) -> Any:  # noqa: ANN401
        """Reverse sequence in-place."""
        from .sequence_interactions import ReverseQuery

        return ReverseQuery(self)

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items."""
        from .shared_interactions import ClearQuery

        return ClearQuery(self)
