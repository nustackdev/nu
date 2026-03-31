# ruff: noqa: D102
"""Bitwise capabilities — protocols + bases.

Atomic:
    BitwiseAndableProtocol/Base: bitand()
    BitwiseOrableProtocol/Base: bitor()
    BitwiseXorableProtocol/Base: __xor__, __rxor__
    BitwiseInvertableProtocol/Base: bitnot()
    ShiftableProtocol/Base: __lshift__, __rshift__

Combined:
    BitwiseProtocol/Base = all of the above
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable


if TYPE_CHECKING:
    from nu.core import Term


__all__ = [
    "BitwiseAndableBase",
    "BitwiseAndableProtocol",
    "BitwiseBase",
    "BitwiseInvertableBase",
    "BitwiseInvertableProtocol",
    "BitwiseOrableBase",
    "BitwiseOrableProtocol",
    "BitwiseProtocol",
    "BitwiseXorableBase",
    "BitwiseXorableProtocol",
    "ShiftableBase",
    "ShiftableProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


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


# =============================================================================
# BASES
# =============================================================================


class BitwiseAndableBase[OperandT, ResultT]:
    """Base for values that support bitwise AND."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitand(self, other: OperandT) -> ResultT:
        """Bitwise AND: self & other (safe method)."""
        from ..morphisms import BitwiseAndOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseAndOp(self, other)))


class BitwiseOrableBase[OperandT, ResultT]:
    """Base for values that support bitwise OR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitor(self, other: OperandT) -> ResultT:
        """Bitwise OR: self | other (safe method)."""
        from ..morphisms import BitwiseOrOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseOrOp(self, other)))


class BitwiseXorableBase[OperandT, ResultT]:
    """Base for values that support bitwise XOR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __xor__(self, other: OperandT) -> ResultT:
        """Bitwise XOR: self ^ other."""
        from ..morphisms import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(self, other)))

    def __rxor__(self, other: OperandT) -> ResultT:
        """Right XOR: other ^ self."""
        from ..morphisms import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(other, self)))


class BitwiseInvertableBase[ResultT]:
    """Base for values that support bitwise NOT."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitnot(self) -> ResultT:
        """Bitwise NOT: ~self (safe method)."""
        from ..morphisms import BitwiseNotOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseNotOp(self)))


class ShiftableBase[OperandT, ResultT]:
    """Base for values that support bit shifting."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __lshift__(self, other: OperandT) -> ResultT:
        """Left shift: self << other."""
        from ..morphisms import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(self, other)))

    def __rlshift__(self, other: OperandT) -> ResultT:
        """Right left shift: other << self."""
        from ..morphisms import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(other, self)))

    def __rshift__(self, other: OperandT) -> ResultT:
        """Right shift: self >> other."""
        from ..morphisms import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(self, other)))

    def __rrshift__(self, other: OperandT) -> ResultT:
        """Right right shift: other >> self."""
        from ..morphisms import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(other, self)))


class BitwiseBase[OperandT, ResultT](
    BitwiseAndableBase[OperandT, ResultT],
    BitwiseOrableBase[OperandT, ResultT],
    BitwiseXorableBase[OperandT, ResultT],
    BitwiseInvertableBase[ResultT],
    ShiftableBase[OperandT, ResultT],
):
    """Full bitwise: bitand(), bitor(), ^, bitnot(), <<, >>."""

    pass
