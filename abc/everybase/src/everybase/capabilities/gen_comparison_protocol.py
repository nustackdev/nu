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
    from everybase.values import BoolValue


__all__ = [
    "ComparableProtocol",
    "EqualableProtocol",
    "OrderableProtocol",
]


@runtime_checkable
class OrderableProtocol[OperandT](Protocol):
    """Protocol for values that support ordering comparisons."""

    def __gt__(self, other: OperandT) -> BoolValue: ...
    def __lt__(self, other: OperandT) -> BoolValue: ...
    def __ge__(self, other: OperandT) -> BoolValue: ...
    def __le__(self, other: OperandT) -> BoolValue: ...


@runtime_checkable
class EqualableProtocol[OperandT](Protocol):
    """Protocol for values that support equality comparison."""

    def eq(self, other: OperandT) -> BoolValue: ...
    def ne(self, other: OperandT) -> BoolValue: ...
    def is_(self, other: OperandT) -> BoolValue: ...


class ComparableProtocol[OperandT](
    OrderableProtocol[OperandT],
    EqualableProtocol[OperandT],
    Protocol,
):
    """Full comparison protocol."""

    ...
