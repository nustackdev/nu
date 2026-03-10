# ruff: noqa: D102
"""Sequence collection — protocols + bases + mutations.

SequenceProtocol/Base = Collection + Sliceable + first/last/join/index/find_index/count
MutableSequenceProtocol/Base = Sequence + append/insert/pop/extend/remove

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

from ..capabilities.collection import SliceableBase, SliceableProtocol
from .collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from everybase.core import Arg, IntArg, StrArg

    from ..values import IntValue, NoneValue, StrValue


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
    def join(self, separator: StrArg) -> StrValue: ...
    def index(self, value: Arg[ElementT]) -> IntValue: ...
    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntValue: ...
    def count(self, value: Arg[ElementT]) -> IntValue: ...


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

    def append(self, value: Arg[ElementT]) -> NoneValue: ...
    def extend(self, other: Arg[Iterable[ElementT]]) -> NoneValue: ...
    def insert(self, index: IntArg, value: Arg[ElementT]) -> NoneValue: ...
    def pop(self, index: IntArg = -1) -> ElementResultT: ...
    def remove(self, value: Arg[ElementT]) -> NoneValue: ...


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
        from ..morphisms import FirstOp

        return cast("ElementResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ElementResultT:
        """Get last element."""
        from ..morphisms import LastOp

        return cast("ElementResultT", self._wrap_element_result(LastOp(self)))

    def join(self, separator: StrArg) -> StrValue:
        """Join string elements."""
        from ..morphisms import JoinOp
        from ..values import StrValue

        return StrValue(JoinOp(self, separator))

    def index(self, value: Arg[ElementT]) -> IntValue:
        """Find index of value."""
        from ..morphisms import IndexOfOp
        from ..values import IntValue

        return IntValue(IndexOfOp(self, value))

    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntValue:
        """Find index of first match."""
        from ..morphisms import FindIndexOp
        from ..values import IntValue

        return IntValue(FindIndexOp(self, predicate))

    def count(self, value: Arg[ElementT]) -> IntValue:
        """Count occurrences."""
        from ..morphisms import CountOp
        from ..values import IntValue

        return IntValue(CountOp(self, value))


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

    def append(self, value: Arg[ElementT]) -> NoneValue:
        """Append item to end of sequence."""
        from ..morphisms.collections.sequence import AppendCmd
        from ..values import NoneValue

        return NoneValue(AppendCmd(self, value))

    def extend(self, other: Arg[Iterable[ElementT]]) -> NoneValue:
        """Extend sequence with elements from iterable."""
        from ..morphisms.collections.sequence import ExtendCmd
        from ..values import NoneValue

        return NoneValue(ExtendCmd(self, other))

    def insert(self, index: IntArg, value: Arg[ElementT]) -> NoneValue:
        """Insert item at index."""
        from ..morphisms.collections.sequence import InsertCmd
        from ..values import NoneValue

        return NoneValue(InsertCmd(self, index, value))

    def pop(self, index: IntArg = -1) -> ElementResultT:
        """Remove and return item at index (default: last)."""
        from ..morphisms.collections.sequence import PopCmd

        return cast("ElementResultT", self._wrap_element_result(PopCmd(self, index)))

    def remove(self, value: Arg[ElementT]) -> NoneValue:
        """Remove first occurrence of value."""
        from ..morphisms.collections.sequence import RemoveValueCmd
        from ..values import NoneValue

        return NoneValue(RemoveValueCmd(self, value))

    def clear(self) -> NoneValue:
        """Remove all items."""
        from ..morphisms.collections.shared import ClearCmd
        from ..values import NoneValue

        return NoneValue(ClearCmd(self))
