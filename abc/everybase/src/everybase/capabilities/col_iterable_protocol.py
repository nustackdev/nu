# ruff: noqa: D102
"""Iterable capability protocol.

IterableProtocol: map_(), filter_(), reduce_(), sum_(), min_(), max_(), any_(), all_()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Callable

    from everybase.values import BoolValue


__all__ = [
    "IterableProtocol",
]


@runtime_checkable
class IterableProtocol[ElementT, ResultT](Protocol):
    """Protocol for values that support functional iteration operations."""

    def map_[R](self, func: Callable[[ElementT], R]) -> ResultT: ...
    def filter_(self, predicate: Callable[[ElementT], bool]) -> ResultT: ...
    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> object: ...
    def sum_(self) -> ResultT: ...
    def min_(self) -> ResultT: ...
    def max_(self) -> ResultT: ...
    def any_(self) -> BoolValue: ...
    def all_(self) -> BoolValue: ...
