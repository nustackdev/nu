# ruff: noqa: D102
"""Sequence capability protocol — Collection + Sliceable + first/last/sorted/...

Follows Python's collections.abc.Sequence pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .col_atoms_protocol import SliceableProtocol
from .col_collection_protocol import CollectionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyabc import BoolArg, StrArg
    from everybase.values import IntValue, StrValue


__all__ = [
    "SequenceProtocol",
]


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
