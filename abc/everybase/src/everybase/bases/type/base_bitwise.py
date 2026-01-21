"""Bitwise base classes for Term types.

This module provides bitwise operation mixins including:
- BitwiseAndableBase - bitand()
- BitwiseOrableBase - bitor()
- BitwiseXorableBase - __xor__, __rxor__
- BitwiseNotableBase - bitnot()
- ShiftableBase - __lshift__, __rshift__ and reverse
- BitwiseBase - Combines all bitwise ops
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from every import Term


__all__ = [
    "BitwiseAndableBase",
    "BitwiseBase",
    "BitwiseNotableBase",
    "BitwiseOrableBase",
    "BitwiseXorableBase",
    "ShiftableBase",
]


class BitwiseAndableBase[OperandT, ResultT]:
    """Base for values that support bitwise AND."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitand(self, other: OperandT) -> ResultT:
        """Bitwise AND: self & other (safe method).

        Args:
            other: Value to AND with

        Returns:
            AND result
        """
        from everybase.ops import BitwiseAndOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseAndOp(self, other)))


class BitwiseOrableBase[OperandT, ResultT]:
    """Base for values that support bitwise OR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitor(self, other: OperandT) -> ResultT:
        """Bitwise OR: self | other (safe method).

        Args:
            other: Value to OR with

        Returns:
            OR result
        """
        from everybase.ops import BitwiseOrOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseOrOp(self, other)))


class BitwiseXorableBase[OperandT, ResultT]:
    """Base for values that support bitwise XOR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __xor__(self, other: OperandT) -> ResultT:
        """Bitwise XOR: self ^ other."""
        from everybase.ops import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(self, other)))

    def __rxor__(self, other: OperandT) -> ResultT:
        """Right XOR: other ^ self."""
        from everybase.ops import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(other, self)))


class BitwiseNotableBase[ResultT]:
    """Base for values that support bitwise NOT."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitnot(self) -> ResultT:
        """Bitwise NOT: ~self (safe method).

        Returns:
            Inverted value
        """
        from everybase.ops import BitwiseNotOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseNotOp(self)))


class ShiftableBase[OperandT, ResultT]:
    """Base for values that support bit shifting."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __lshift__(self, other: OperandT) -> ResultT:
        """Left shift: self << other."""
        from everybase.ops import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(self, other)))

    def __rlshift__(self, other: OperandT) -> ResultT:
        """Right left shift: other << self."""
        from everybase.ops import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(other, self)))

    def __rshift__(self, other: OperandT) -> ResultT:
        """Right shift: self >> other."""
        from everybase.ops import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(self, other)))

    def __rrshift__(self, other: OperandT) -> ResultT:
        """Right right shift: other >> self."""
        from everybase.ops import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(other, self)))


class BitwiseBase[OperandT, ResultT](
    BitwiseAndableBase[OperandT, ResultT],
    BitwiseOrableBase[OperandT, ResultT],
    BitwiseXorableBase[OperandT, ResultT],
    BitwiseNotableBase[ResultT],
    ShiftableBase[OperandT, ResultT],
):
    """Full bitwise operations: bitand(), bitor(), ^, bitnot(), <<, >>.

    Use this for integer types that support bitwise operations.
    """

    pass
