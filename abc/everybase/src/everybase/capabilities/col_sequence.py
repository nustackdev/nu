"""Sequence capability — combined collection trait.

Sequence = Lengthable + Sliceable + Containable + Iterable + first/last/reversed/sorted/join/index/count
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .col_access import Containable, Lengthable, Sliceable
from .col_iterable import Iterable


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyabc import BoolArg, StrArg
    from everybase.py import IntRef, StrRef


__all__ = [
    "Sequence",
]


class Sequence[ElementT, ResultT](
    Lengthable,
    Sliceable[ResultT],
    Containable[ElementT],
    Iterable[ElementT, ResultT],
):
    """Combined trait for sequence-like values."""

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

    def join(self, separator: StrArg) -> StrRef:
        """Join string elements."""
        from everybase.morphisms import JoinOp
        from everybase.py import StrRef

        return StrRef(JoinOp(self, separator))

    def index(self, value: ElementT) -> IntRef:
        """Find index of value."""
        from everybase.morphisms import IndexOfOp
        from everybase.py import IntRef

        return IntRef(IndexOfOp(self, value))

    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntRef:
        """Find index of first match."""
        from everybase.morphisms import FindIndexOp
        from everybase.py import IntRef

        return IntRef(FindIndexOp(self, predicate))

    def count(self, value: ElementT) -> IntRef:
        """Count occurrences."""
        from everybase.morphisms import CountOp
        from everybase.py import IntRef

        return IntRef(CountOp(self, value))
