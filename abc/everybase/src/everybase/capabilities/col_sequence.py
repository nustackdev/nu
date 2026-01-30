# ruff: noqa: D102
"""Sequence capability — protocols + bases + mutations.

SequenceProtocol/Base = Collection + Sliceable + first/last/sorted/join/index/find_index/count
MutableSequenceProtocol/Base = Sequence + append/insert/pop

Follows Python's collections.abc.Sequence / MutableSequence pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from .col_atoms import SliceableBase, SliceableProtocol
from .col_collection import CollectionBase, CollectionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from everyabc import BoolArg, StrArg
    from everybase.values import IntValue, StrValue


__all__ = [
    "MutableSequenceBase",
    "MutableSequenceProtocol",
    "SequenceBase",
    "SequenceProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


class SequenceProtocol[ElementT, ResultT](
    CollectionProtocol[ElementT, ResultT],
    SliceableProtocol[ResultT],
    Protocol,
):
    """Protocol for sequence values — like collections.abc.Sequence."""

    def first(self) -> ResultT: ...
    def last(self) -> ResultT: ...
    def reversed_(self) -> ResultT: ...
    def sorted_(self, reverse: BoolArg = False) -> ResultT: ...
    def join(self, separator: StrArg) -> StrValue: ...
    def index(self, value: ElementT) -> IntValue: ...
    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntValue: ...
    def count(self, value: ElementT) -> IntValue: ...


class MutableSequenceProtocol[ElementT, ResultT](
    SequenceProtocol[ElementT, ResultT],
    Protocol,
):
    """Protocol for mutable sequence values — like collections.abc.MutableSequence."""

    def append(self, value: ElementT) -> ResultT: ...
    def extend(self, other: Iterable[ElementT]) -> ResultT: ...
    def insert(self, index: int, value: ElementT) -> ResultT: ...
    def pop(self, index: int = -1) -> ResultT: ...
    def remove(self, value: ElementT) -> ResultT: ...


# =============================================================================
# BASES
# =============================================================================


class SequenceBase[ElementT, ResultT](
    CollectionBase[ElementT, ResultT],
    SliceableBase[ResultT],
):
    """Base for sequence values — like collections.abc.Sequence."""

    def first(self) -> ResultT:
        """Get first element."""
        from everybase.morphisms import FirstOp

        return cast("ResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ResultT:
        """Get last element."""
        from everybase.morphisms import LastOp

        return cast("ResultT", self._wrap_element_result(LastOp(self)))

    def reversed_(self) -> ResultT:
        """Get reversed sequence."""
        from everybase.morphisms import ReversedOp

        return cast("ResultT", self._wrap_sliceable_result(ReversedOp(self)))

    def sorted_(self, reverse: BoolArg = False) -> ResultT:
        """Get sorted sequence."""
        from everybase.morphisms import SortedOp

        return cast("ResultT", self._wrap_sliceable_result(SortedOp(self, reverse=reverse)))

    def join(self, separator: StrArg) -> StrValue:
        """Join string elements."""
        from everybase.morphisms import JoinOp
        from everybase.values import StrValue

        return StrValue(JoinOp(self, separator))

    def index(self, value: ElementT) -> IntValue:
        """Find index of value."""
        from everybase.morphisms import IndexOfOp
        from everybase.values import IntValue

        return IntValue(IndexOfOp(self, value))

    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntValue:
        """Find index of first match."""
        from everybase.morphisms import FindIndexOp
        from everybase.values import IntValue

        return IntValue(FindIndexOp(self, predicate))

    def count(self, value: ElementT) -> IntValue:
        """Count occurrences."""
        from everybase.morphisms import CountOp
        from everybase.values import IntValue

        return IntValue(CountOp(self, value))


class MutableSequenceBase[ElementT, ResultT](
    SequenceBase[ElementT, ResultT],
):
    """Base for mutable sequence values — like collections.abc.MutableSequence."""

    def append(self, value: ElementT) -> ResultT:
        """Append item to end of sequence."""
        from everybase.morphisms.abc_sequence import AppendCmd

        return cast("ResultT", self._wrap_sliceable_result(AppendCmd(self, value)))

    def extend(self, other: Iterable[ElementT]) -> ResultT:
        """Extend sequence with elements from iterable."""
        from everybase.morphisms.abc_sequence import ExtendCmd

        return cast("ResultT", self._wrap_sliceable_result(ExtendCmd(self, other)))

    def insert(self, index: int, value: ElementT) -> ResultT:
        """Insert item at index."""
        from everybase.morphisms.abc_sequence import InsertCmd

        return cast("ResultT", self._wrap_sliceable_result(InsertCmd(self, index, value)))

    def pop(self, index: int = -1) -> ResultT:
        """Remove and return item at index (default: last)."""
        from everybase.morphisms.abc_sequence import PopCmd

        return cast("ResultT", self._wrap_element_result(PopCmd(self, index)))

    def remove(self, value: ElementT) -> ResultT:
        """Remove first occurrence of value."""
        from everybase.morphisms.abc_sequence import RemoveValueCmd

        return cast("ResultT", self._wrap_sliceable_result(RemoveValueCmd(self, value)))
