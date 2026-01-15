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

from ..conversion import literal


if TYPE_CHECKING:
    from .. import Term


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
        from ..comp import BitwiseAndOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseAndOp(self, literal(other))))


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
        from ..comp import BitwiseOrOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseOrOp(self, literal(other))))


class BitwiseXorableBase[OperandT, ResultT]:
    """Base for values that support bitwise XOR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __xor__(self, other: OperandT) -> ResultT:
        """Bitwise XOR: self ^ other."""
        from ..comp import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(self, literal(other))))

    def __rxor__(self, other: OperandT) -> ResultT:
        """Right XOR: other ^ self."""
        from ..comp import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(literal(other), self)))


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
        from ..comp import BitwiseNotOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseNotOp(self)))


class ShiftableBase[OperandT, ResultT]:
    """Base for values that support bit shifting."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __lshift__(self, other: OperandT) -> ResultT:
        """Left shift: self << other."""
        from ..comp import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(self, literal(other))))

    def __rlshift__(self, other: OperandT) -> ResultT:
        """Right left shift: other << self."""
        from ..comp import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(literal(other), self)))

    def __rshift__(self, other: OperandT) -> ResultT:
        """Right shift: self >> other."""
        from ..comp import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(self, literal(other))))

    def __rrshift__(self, other: OperandT) -> ResultT:
        """Right right shift: other >> self."""
        from ..comp import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(literal(other), self)))


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
