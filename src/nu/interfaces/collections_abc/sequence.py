# ruff: noqa: D102
"""Sequence collection — protocols + bases + mutations.

SequenceProtocol/Base = Collection + Sliceable + first/last/index/count/reversed
MutableSequenceProtocol/Base = Sequence + append/insert/pop/extend/remove/reverse

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

from typing import TYPE_CHECKING, Protocol, cast

from .collection import CollectionBase, CollectionProtocol
from .sliceable import SliceableBase, SliceableProtocol


if TYPE_CHECKING:
    from collections.abc import Iterable

    from nu.terms import Arg, IntArg

    from nu.interfaces.primitives import IntI, NoneI


__all__ = [
    "MutableSequenceBase",
    "MutableSequenceProtocol",
    "SequenceBase",
    "SequenceProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


class SequenceProtocol[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionProtocol[ElementT, CollectionResultT, ElementResultT],
    SliceableProtocol[CollectionResultT],
    Protocol,
):
    """Protocol for sequence values — like collections.abc.Sequence.

    Type Parameters:
        CollectionT: Native Python collection type (list[int], tuple[str, ...])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (map_, filter_, reversed_, sorted_)
        ElementResultT: Result for element-level ops (first, last, sum_, min_, max_)
    """

    def first(self) -> ElementResultT: ...
    def last(self) -> ElementResultT: ...
    def index(self, value: Arg[ElementT]) -> IntI: ...
    def count(self, value: Arg[ElementT]) -> IntI: ...
    def reversed(self) -> CollectionResultT: ...


class MutableSequenceProtocol[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SequenceProtocol[CollectionT, ElementT, CollectionResultT, ElementResultT],
    Protocol,
):
    """Protocol for mutable sequence values — like collections.abc.MutableSequence.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (append, extend, insert, remove)
        ElementResultT: Result for element-level ops (pop)
    """

    def append(self, value: Arg[ElementT]) -> NoneI: ...
    def extend(self, other: Arg[Iterable[ElementT]]) -> NoneI: ...
    def insert(self, index: IntArg, value: Arg[ElementT]) -> NoneI: ...
    def pop(self, index: IntArg = -1) -> ElementResultT: ...
    def remove(self, value: Arg[ElementT]) -> NoneI: ...
    def reverse(self) -> NoneI: ...


# =============================================================================
# BASES
# =============================================================================


class SequenceBase[CollectionT, ElementT, CollectionResultT, ElementResultT](
    CollectionBase[ElementT, CollectionResultT, ElementResultT],
    SliceableBase[CollectionResultT],
):
    """Base for sequence values — like collections.abc.Sequence.

    Type Parameters:
        CollectionT: Native Python collection type (list[int], tuple[str, ...])
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (map_, filter_, reversed_, sorted_)
        ElementResultT: Result for element-level ops (first, last, sum_, min_, max_)
    """

    def first(self) -> ElementResultT:
        """Get first element."""
        from .sequence_ops import FirstOp

        return cast("ElementResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ElementResultT:
        """Get last element."""
        from .sequence_ops import LastOp

        return cast("ElementResultT", self._wrap_element_result(LastOp(self)))

    def index(self, value: Arg[ElementT]) -> IntI:
        """Find index of value."""
        from .sequence_ops import IndexOfOp
        from nu.interfaces.primitives import IntI

        return IntI(IndexOfOp(self, value))

    def count(self, value: Arg[ElementT]) -> IntI:
        """Count occurrences."""
        from .sequence_ops import CountOp
        from nu.interfaces.primitives import IntI

        return IntI(CountOp(self, value))

    def reversed(self) -> CollectionResultT:
        """Reversed copy of this sequence."""
        from nu.ops.itertools.transform import ReversedOp

        return cast("CollectionResultT", self._wrap_iterable_result(ReversedOp(self)))


class MutableSequenceBase[CollectionT, ElementT, CollectionResultT, ElementResultT](
    SequenceBase[CollectionT, ElementT, CollectionResultT, ElementResultT],
):
    """Base for mutable sequence values — like collections.abc.MutableSequence.

    Type Parameters:
        CollectionT: Native Python collection type
        ElementT: Native Python element type
        CollectionResultT: Result for collection-level ops (append, extend, insert, remove)
        ElementResultT: Result for element-level ops (pop)
    """

    def append(self, value: Arg[ElementT]) -> NoneI:
        """Append item to end of sequence."""
        from .sequence_ops import AppendCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(AppendCmd(self, value))

    def extend(self, other: Arg[Iterable[ElementT]]) -> NoneI:
        """Extend sequence with elements from iterable."""
        from .sequence_ops import ExtendCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(ExtendCmd(self, other))

    def insert(self, index: IntArg, value: Arg[ElementT]) -> NoneI:
        """Insert item at index."""
        from .sequence_ops import InsertCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(InsertCmd(self, index, value))

    def pop(self, index: IntArg = -1) -> ElementResultT:
        """Remove and return item at index (default: last)."""
        from .sequence_ops import PopCmd

        return cast("ElementResultT", self._wrap_element_result(PopCmd(self, index)))

    def remove(self, value: Arg[ElementT]) -> NoneI:
        """Remove first occurrence of value."""
        from .sequence_ops import RemoveValueCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(RemoveValueCmd(self, value))

    def reverse(self) -> NoneI:
        """Reverse sequence in-place."""
        from .sequence_ops import ReverseCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(ReverseCmd(self))

    def clear(self) -> NoneI:
        """Remove all items."""
        from .shared_ops import ClearCmd
        from nu.interfaces.primitives import NoneI

        return NoneI(ClearCmd(self))
