"""Arithmetic base classes for Term types.

This module provides arithmetic operation mixins including:
- AddableBase, SubtractableBase, NegatableBase
- MultiplyableBase, DivisibleBase, ModuloableBase, PowerableBase
- AdditiveBase, MultiplicativeBase, NumericBase (combined bases)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..conversion import literal


if TYPE_CHECKING:
    from .. import Term


__all__ = [
    # Atomic arithmetic bases
    "AddableBase",
    # Combined arithmetic bases
    "AdditiveBase",
    "DivisibleBase",
    "ModuloableBase",
    "MultiplicativeBase",
    "MultiplyableBase",
    "NegatableBase",
    "NumericBase",
    "PowerableBase",
    "SubtractableBase",
]


class AddableBase[OperandT, ResultT]:
    """Base for values that support addition."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __add__(self, other: OperandT) -> ResultT:
        """Addition: self + other."""
        from ..comp import AddOp

        return cast("ResultT", self._wrap_arithmetic_result(AddOp(self, literal(other))))

    def __radd__(self, other: OperandT) -> ResultT:
        """Right addition: other + self."""
        from ..comp import AddOp

        return cast("ResultT", self._wrap_arithmetic_result(AddOp(literal(other), self)))


class SubtractableBase[OperandT, ResultT]:
    """Base for values that support subtraction."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __sub__(self, other: OperandT) -> ResultT:
        """Subtraction: self - other."""
        from ..comp import SubOp

        return cast("ResultT", self._wrap_arithmetic_result(SubOp(self, literal(other))))

    def __rsub__(self, other: OperandT) -> ResultT:
        """Right subtraction: other - self."""
        from ..comp import SubOp

        return cast("ResultT", self._wrap_arithmetic_result(SubOp(literal(other), self)))


class NegatableBase[ResultT]:
    """Base for values that support unary negation, positive, and abs."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __neg__(self) -> ResultT:
        """Negation: -self."""
        from ..comp import NegOp

        return cast("ResultT", self._wrap_arithmetic_result(NegOp(self)))

    def __pos__(self) -> ResultT:
        """Positive: +self."""
        from ..comp import PosOp

        return cast("ResultT", self._wrap_arithmetic_result(PosOp(self)))

    def __abs__(self) -> ResultT:
        """Absolute value: abs(self)."""
        from ..comp import AbsOp

        return cast("ResultT", self._wrap_arithmetic_result(AbsOp(self)))


class MultiplyableBase[OperandT, ResultT]:
    """Base for values that support multiplication."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __mul__(self, other: OperandT) -> ResultT:
        """Multiplication: self * other."""
        from ..comp import MulOp

        return cast("ResultT", self._wrap_arithmetic_result(MulOp(self, literal(other))))

    def __rmul__(self, other: OperandT) -> ResultT:
        """Right multiplication: other * self."""
        from ..comp import MulOp

        return cast("ResultT", self._wrap_arithmetic_result(MulOp(literal(other), self)))


class DivisibleBase[OperandT, ResultT]:
    """Base for values that support division (true and floor)."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __truediv__(self, other: OperandT) -> ResultT:
        """Division: self / other."""
        from ..comp import DivOp

        return cast("ResultT", self._wrap_arithmetic_result(DivOp(self, literal(other))))

    def __rtruediv__(self, other: OperandT) -> ResultT:
        """Right division: other / self."""
        from ..comp import DivOp

        return cast("ResultT", self._wrap_arithmetic_result(DivOp(literal(other), self)))

    def __floordiv__(self, other: OperandT) -> ResultT:
        """Floor division: self // other."""
        from ..comp import FloorDivOp

        return cast("ResultT", self._wrap_arithmetic_result(FloorDivOp(self, literal(other))))

    def __rfloordiv__(self, other: OperandT) -> ResultT:
        """Right floor division: other // self."""
        from ..comp import FloorDivOp

        return cast("ResultT", self._wrap_arithmetic_result(FloorDivOp(literal(other), self)))


class ModuloableBase[OperandT, ResultT]:
    """Base for values that support modulo operation."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __mod__(self, other: OperandT) -> ResultT:
        """Modulo: self % other."""
        from ..comp import ModOp

        return cast("ResultT", self._wrap_arithmetic_result(ModOp(self, literal(other))))

    def __rmod__(self, other: OperandT) -> ResultT:
        """Right modulo: other % self."""
        from ..comp import ModOp

        return cast("ResultT", self._wrap_arithmetic_result(ModOp(literal(other), self)))


class PowerableBase[OperandT, ResultT]:
    """Base for values that support exponentiation."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __pow__(self, other: OperandT) -> ResultT:
        """Power: self ** other."""
        from ..comp import PowOp

        return cast("ResultT", self._wrap_arithmetic_result(PowOp(self, literal(other))))

    def __rpow__(self, other: OperandT) -> ResultT:
        """Right power: other ** self."""
        from ..comp import PowOp

        return cast("ResultT", self._wrap_arithmetic_result(PowOp(literal(other), self)))


# =============================================================================
# COMBINED ARITHMETIC BASES
# =============================================================================


class AdditiveBase[OperandT, ResultT](
    AddableBase[OperandT, ResultT],
    SubtractableBase[OperandT, ResultT],
    NegatableBase[ResultT],
):
    """Combined base for additive operations: +, -, neg, pos, abs.

    Use this for types like datetime.timedelta that support addition/subtraction
    but not multiplication/division.
    """

    pass


class MultiplicativeBase[OperandT, ResultT](
    MultiplyableBase[OperandT, ResultT],
    DivisibleBase[OperandT, ResultT],
    ModuloableBase[OperandT, ResultT],
    PowerableBase[OperandT, ResultT],
):
    """Combined base for multiplicative operations: *, /, //, %, **.

    Use this for types that support multiplication family operations.
    """

    pass


class NumericBase[OperandT, ResultT](
    AdditiveBase[OperandT, ResultT],
    MultiplicativeBase[OperandT, ResultT],
):
    """Full arithmetic operations: +, -, *, /, //, %, **, neg, pos, abs.

    Use this for int, float, Decimal, Fraction, and similar numeric types.
    """

    pass
