"""Arithmetic capability protocols.

Atomic:
    AddableProtocol, SubtractableProtocol, NegatableProtocol,
    MultiplyableProtocol, DivisibleProtocol, ModuloableProtocol, PowerableProtocol

Combined:
    AdditiveProtocol = Addable + Subtractable + Negatable
    MultiplicativeProtocol = Multiplyable + Divisible + Moduloable + Powerable
    NumericProtocol = Additive + Multiplicative
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


__all__ = [
    "AddableProtocol",
    "AdditiveProtocol",
    "DivisibleProtocol",
    "ModuloableProtocol",
    "MultiplicativeProtocol",
    "MultiplyableProtocol",
    "NegatableProtocol",
    "NumericProtocol",
    "PowerableProtocol",
    "SubtractableProtocol",
]


@runtime_checkable
class AddableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support addition."""

    def __add__(self, other: OperandT) -> ResultT: ...
    def __radd__(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class SubtractableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support subtraction."""

    def __sub__(self, other: OperandT) -> ResultT: ...
    def __rsub__(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class NegatableProtocol[ResultT](Protocol):
    """Protocol for values that support unary negation, positive, and abs."""

    def __neg__(self) -> ResultT: ...
    def __pos__(self) -> ResultT: ...
    def __abs__(self) -> ResultT: ...


@runtime_checkable
class MultiplyableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support multiplication."""

    def __mul__(self, other: OperandT) -> ResultT: ...
    def __rmul__(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class DivisibleProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support division (true and floor)."""

    def __truediv__(self, other: OperandT) -> ResultT: ...
    def __rtruediv__(self, other: OperandT) -> ResultT: ...
    def __floordiv__(self, other: OperandT) -> ResultT: ...
    def __rfloordiv__(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class ModuloableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support modulo operation."""

    def __mod__(self, other: OperandT) -> ResultT: ...
    def __rmod__(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class PowerableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support exponentiation."""

    def __pow__(self, other: OperandT) -> ResultT: ...
    def __rpow__(self, other: OperandT) -> ResultT: ...


class AdditiveProtocol[OperandT, ResultT](
    AddableProtocol[OperandT, ResultT],
    SubtractableProtocol[OperandT, ResultT],
    NegatableProtocol[ResultT],
    Protocol,
):
    """Combined protocol for additive operations."""

    ...


class MultiplicativeProtocol[OperandT, ResultT](
    MultiplyableProtocol[OperandT, ResultT],
    DivisibleProtocol[OperandT, ResultT],
    ModuloableProtocol[OperandT, ResultT],
    PowerableProtocol[OperandT, ResultT],
    Protocol,
):
    """Combined protocol for multiplicative operations."""

    ...


class NumericProtocol[OperandT, ResultT](
    AdditiveProtocol[OperandT, ResultT],
    MultiplicativeProtocol[OperandT, ResultT],
    Protocol,
):
    """Full arithmetic protocol."""

    ...
