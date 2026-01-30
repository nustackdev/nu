# ruff: noqa: D102
"""Comparison capability protocols.

Atomic:
    OrderableProtocol: __gt__, __lt__, __ge__, __le__
    EqualableProtocol: eq(), ne(), is_()

Combined:
    ComparableProtocol = Orderable + Equalable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from everybase.py import BoolRef


__all__ = [
    "ComparableProtocol",
    "EqualableProtocol",
    "OrderableProtocol",
]


@runtime_checkable
class OrderableProtocol[OperandT](Protocol):
    """Protocol for values that support ordering comparisons."""

    def __gt__(self, other: OperandT) -> BoolRef: ...
    def __lt__(self, other: OperandT) -> BoolRef: ...
    def __ge__(self, other: OperandT) -> BoolRef: ...
    def __le__(self, other: OperandT) -> BoolRef: ...


@runtime_checkable
class EqualableProtocol[OperandT](Protocol):
    """Protocol for values that support equality comparison."""

    def eq(self, other: OperandT) -> BoolRef: ...
    def ne(self, other: OperandT) -> BoolRef: ...
    def is_(self, other: OperandT) -> BoolRef: ...


class ComparableProtocol[OperandT](
    OrderableProtocol[OperandT],
    EqualableProtocol[OperandT],
    Protocol,
):
    """Full comparison protocol."""

    ...
