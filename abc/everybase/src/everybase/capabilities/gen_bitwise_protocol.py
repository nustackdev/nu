# ruff: noqa: D102
"""Bitwise capability protocols.

Atomic:
    BitwiseAndableProtocol: bitand()
    BitwiseOrableProtocol: bitor()
    BitwiseXorableProtocol: __xor__, __rxor__
    BitwiseInvertableProtocol: bitnot()
    ShiftableProtocol: __lshift__, __rshift__

Combined:
    BitwiseProtocol = all of the above
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


__all__ = [
    "BitwiseAndableProtocol",
    "BitwiseInvertableProtocol",
    "BitwiseOrableProtocol",
    "BitwiseProtocol",
    "BitwiseXorableProtocol",
    "ShiftableProtocol",
]


@runtime_checkable
class BitwiseAndableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support bitwise AND."""

    def bitand(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class BitwiseOrableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support bitwise OR."""

    def bitor(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class BitwiseXorableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support bitwise XOR."""

    def __xor__(self, other: OperandT) -> ResultT: ...
    def __rxor__(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class BitwiseInvertableProtocol[ResultT](Protocol):
    """Protocol for values that support bitwise NOT."""

    def bitnot(self) -> ResultT: ...


@runtime_checkable
class ShiftableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support bit shifting."""

    def __lshift__(self, other: OperandT) -> ResultT: ...
    def __rshift__(self, other: OperandT) -> ResultT: ...


class BitwiseProtocol[OperandT, ResultT](
    BitwiseAndableProtocol[OperandT, ResultT],
    BitwiseOrableProtocol[OperandT, ResultT],
    BitwiseXorableProtocol[OperandT, ResultT],
    BitwiseInvertableProtocol[ResultT],
    ShiftableProtocol[OperandT, ResultT],
    Protocol,
):
    """Full bitwise protocol."""

    ...
