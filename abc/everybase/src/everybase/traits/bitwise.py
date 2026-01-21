"""Bitwise capability traits for refs.

Atomic traits:
- BitwiseAndable: bitand()
- BitwiseOrable: bitor()
- BitwiseXorable: __xor__, __rxor__
- BitwiseInvertable: bitnot()
- Shiftable: __lshift__, __rshift__

Combined traits:
- Bitwise = BitwiseAndable + BitwiseOrable + BitwiseXorable + BitwiseInvertable + Shiftable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from every import Term


__all__ = [
    "Bitwise",
    "BitwiseAndable",
    "BitwiseInvertable",
    "BitwiseOrable",
    "BitwiseXorable",
    "Shiftable",
]


class BitwiseAndable[OperandT, ResultT]:
    """Trait for values that support bitwise AND."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitand(self, other: OperandT) -> ResultT:
        """Bitwise AND: self & other (safe method)."""
        from everybase.morphisms import BitwiseAndOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseAndOp(self, other)))


class BitwiseOrable[OperandT, ResultT]:
    """Trait for values that support bitwise OR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitor(self, other: OperandT) -> ResultT:
        """Bitwise OR: self | other (safe method)."""
        from everybase.morphisms import BitwiseOrOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseOrOp(self, other)))


class BitwiseXorable[OperandT, ResultT]:
    """Trait for values that support bitwise XOR."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __xor__(self, other: OperandT) -> ResultT:
        """Bitwise XOR: self ^ other."""
        from everybase.morphisms import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(self, other)))

    def __rxor__(self, other: OperandT) -> ResultT:
        """Right XOR: other ^ self."""
        from everybase.morphisms import XorOp

        return cast("ResultT", self._wrap_bitwise_result(XorOp(other, self)))


class BitwiseInvertable[ResultT]:
    """Trait for values that support bitwise NOT."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def bitnot(self) -> ResultT:
        """Bitwise NOT: ~self (safe method)."""
        from everybase.morphisms import BitwiseNotOp

        return cast("ResultT", self._wrap_bitwise_result(BitwiseNotOp(self)))


class Shiftable[OperandT, ResultT]:
    """Trait for values that support bit shifting."""

    def _wrap_bitwise_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __lshift__(self, other: OperandT) -> ResultT:
        """Left shift: self << other."""
        from everybase.morphisms import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(self, other)))

    def __rlshift__(self, other: OperandT) -> ResultT:
        """Right left shift: other << self."""
        from everybase.morphisms import LShiftOp

        return cast("ResultT", self._wrap_bitwise_result(LShiftOp(other, self)))

    def __rshift__(self, other: OperandT) -> ResultT:
        """Right shift: self >> other."""
        from everybase.morphisms import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(self, other)))

    def __rrshift__(self, other: OperandT) -> ResultT:
        """Right right shift: other >> self."""
        from everybase.morphisms import RShiftOp

        return cast("ResultT", self._wrap_bitwise_result(RShiftOp(other, self)))


class Bitwise[OperandT, ResultT](
    BitwiseAndable[OperandT, ResultT],
    BitwiseOrable[OperandT, ResultT],
    BitwiseXorable[OperandT, ResultT],
    BitwiseInvertable[ResultT],
    Shiftable[OperandT, ResultT],
):
    """Full bitwise: bitand(), bitor(), ^, bitnot(), <<, >>."""

    pass
