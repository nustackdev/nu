# ruff: noqa: D102
"""Atomic collection capability protocols.

ContainableProtocol: contains()       — like collections.abc.Container
LengthableProtocol: len_()            — like collections.abc.Sized
IndexableProtocol: __getitem__        — index/key access
SliceableProtocol: slice_()           — slice access
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from everyabc import IntArg
    from everybase.py import BoolRef, IntRef


__all__ = [
    "ContainableProtocol",
    "IndexableProtocol",
    "LengthableProtocol",
    "SliceableProtocol",
]


@runtime_checkable
class ContainableProtocol[ItemT](Protocol):
    """Protocol for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolRef: ...


@runtime_checkable
class LengthableProtocol(Protocol):
    """Protocol for values that have a length."""

    def len_(self) -> IntRef: ...


@runtime_checkable
class IndexableProtocol[KeyT, ResultValue](Protocol):
    """Protocol for values that support index/key access."""

    def __getitem__(self, key: KeyT) -> ResultValue: ...


@runtime_checkable
class SliceableProtocol[ResultT](Protocol):
    """Protocol for values that support slicing."""

    def slice_(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT: ...
