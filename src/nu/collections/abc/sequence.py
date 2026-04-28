"""Sequence collection — bases + mutations.

SequenceI = Collection + Sliceable + first/last/index/count/reversed
MutableSequenceI = Sequence + append/insert/pop/extend/remove/reverse

Sorted/Reversed are standalone functions in ``abc.fn``.

Follows Python's collections.abc.Sequence / MutableSequence pattern.

Type Parameters:
    CollectionT: Native Python collection type (list[int], tuple[str, ...], etc.)
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
        (slice_, append, insert, extend, remove)
    ElementResultT: Wrapped result for element-level operations
        (first, last, pop)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .collection import CollectionI
from .sliceable import SliceableI


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.primitives import IntI, NoneI
    from nu.terms import Arg, IntArg


__all__ = [
    "MutableSequenceI",
    "SequenceI",
]


class SequenceI[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionI[ElementT, CollectionResultT, ElementResultT],
    SliceableI[CollectionResultT],
):
    """Base for sequence values — like collections.abc.Sequence.

    Type Parameters:
        CollectionT: Native Python collection type (list[int], tuple[str, ...])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (map_, filter_, reversed_, sorted_)
        ElementResultT: Result for element-level ops (first, last, sum_, min_, max_)
    """

    def first_elem(self) -> ElementResultT:
        """Get first element."""
        from .sequence_ops import FirstOp

        return cast("ElementResultT", self._wrap_element_result(FirstOp(self)))

    def last_elem(self) -> ElementResultT:
        """Get last element."""
        from .sequence_ops import LastOp

        return cast("ElementResultT", self._wrap_element_result(LastOp(self)))

    def index(self, value: Arg[ElementT]) -> IntI:
        """Find index of value."""
        from nu.primitives import IntI

        from .sequence_ops import IndexOfOp

        return IntI(IndexOfOp(self, value))

    def count(self, value: Arg[ElementT]) -> IntI:
        """Count occurrences."""
        from nu.primitives import IntI

        from .sequence_ops import CountOp

        return IntI(CountOp(self, value))

    def reversed(self) -> CollectionResultT:
        """Reversed copy of this sequence."""
        from nu.interactions import Reversed

        return cast("CollectionResultT", self._wrap_iterable_result(Reversed(self)))


class MutableSequenceI[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SequenceI[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable sequence values — like collections.abc.MutableSequence.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (append, extend, insert, remove)
        ElementResultT: Result for element-level ops (pop)
    """

    def append(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Append item to end of sequence."""
        from .sequence_ops import AppendCmd

        return AppendCmd(self, value)

    def extend(self, other: Arg[Iterable[ElementT]]) -> Any:  # noqa: ANN401
        """Extend sequence with elements from iterable."""
        from .sequence_ops import ExtendCmd

        return ExtendCmd(self, other)

    def insert(self, index: IntArg, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Insert item at index."""
        from .sequence_ops import InsertCmd

        return InsertCmd(self, index, value)

    def pop(self, index: IntArg = -1) -> ElementResultT:
        """Remove and return item at index (default: last)."""
        from .sequence_ops import PopCmd

        return cast("ElementResultT", self._wrap_element_result(PopCmd(self, index)))

    def remove(self, value: Arg[ElementT]) -> Any:  # noqa: ANN401
        """Remove first occurrence of value."""
        from .sequence_ops import RemoveValueCmd

        return RemoveValueCmd(self, value)

    def reverse(self) -> Any:  # noqa: ANN401
        """Reverse sequence in-place."""
        from .sequence_ops import ReverseCmd

        return ReverseCmd(self)

    def clear(self) -> Any:  # noqa: ANN401
        """Remove all items."""
        from .shared_ops import ClearCmd

        return ClearCmd(self)
