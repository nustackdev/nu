"""Arithmetic capabilities — protocols + bases.

Atomic:
    AddableProtocol/Base, SubtractableProtocol/Base, NegatableProtocol/Base,
    MultiplyableProtocol/Base, DivisibleProtocol/Base, ModuloableProtocol/Base, PowerableProtocol/Base

Combined:
    AdditiveProtocol/Base = Addable + Subtractable + Negatable
    MultiplicativeProtocol/Base = Multiplyable + Divisible + Moduloable + Powerable
    NumericProtocol/Base = Additive + Multiplicative
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable


if TYPE_CHECKING:
    from everyabc import Term


__all__ = [
    "AddableBase",
    "AddableProtocol",
    "AdditiveBase",
    "AdditiveProtocol",
    "DivisibleBase",
    "DivisibleProtocol",
    "ModuloableBase",
    "ModuloableProtocol",
    "MultiplicativeBase",
    "MultiplicativeProtocol",
    "MultiplyableBase",
    "MultiplyableProtocol",
    "NegatableBase",
    "NegatableProtocol",
    "NumericBase",
    "NumericProtocol",
    "PowerableBase",
    "PowerableProtocol",
    "SubtractableBase",
    "SubtractableProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


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


# =============================================================================
# BASES
# =============================================================================


class AddableBase[OperandT, ResultT]:
    """Base for values that support addition."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __add__(self, other: OperandT) -> ResultT:
        """Addition: self + other."""
        from everybase.morphisms import AddOp

        return cast("ResultT", self._wrap_arithmetic_result(AddOp(self, other)))

    def __radd__(self, other: OperandT) -> ResultT:
        """Right addition: other + self."""
        from everybase.morphisms import AddOp

        return cast("ResultT", self._wrap_arithmetic_result(AddOp(other, self)))


class SubtractableBase[OperandT, ResultT]:
    """Base for values that support subtraction."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __sub__(self, other: OperandT) -> ResultT:
        """Subtraction: self - other."""
        from everybase.morphisms import SubOp

        return cast("ResultT", self._wrap_arithmetic_result(SubOp(self, other)))

    def __rsub__(self, other: OperandT) -> ResultT:
        """Right subtraction: other - self."""
        from everybase.morphisms import SubOp

        return cast("ResultT", self._wrap_arithmetic_result(SubOp(other, self)))


class NegatableBase[ResultT]:
    """Base for values that support unary negation, positive, and abs."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __neg__(self) -> ResultT:
        """Negation: -self."""
        from everybase.morphisms import NegOp

        return cast("ResultT", self._wrap_arithmetic_result(NegOp(self)))

    def __pos__(self) -> ResultT:
        """Positive: +self."""
        from everybase.morphisms import PosOp

        return cast("ResultT", self._wrap_arithmetic_result(PosOp(self)))

    def __abs__(self) -> ResultT:
        """Absolute value: abs(self)."""
        from everybase.morphisms import AbsOp

        return cast("ResultT", self._wrap_arithmetic_result(AbsOp(self)))


class MultiplyableBase[OperandT, ResultT]:
    """Base for values that support multiplication."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __mul__(self, other: OperandT) -> ResultT:
        """Multiplication: self * other."""
        from everybase.morphisms import MulOp

        return cast("ResultT", self._wrap_arithmetic_result(MulOp(self, other)))

    def __rmul__(self, other: OperandT) -> ResultT:
        """Right multiplication: other * self."""
        from everybase.morphisms import MulOp

        return cast("ResultT", self._wrap_arithmetic_result(MulOp(other, self)))


class DivisibleBase[OperandT, ResultT]:
    """Base for values that support division (true and floor)."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __truediv__(self, other: OperandT) -> ResultT:
        """Division: self / other."""
        from everybase.morphisms import DivOp

        return cast("ResultT", self._wrap_arithmetic_result(DivOp(self, other)))

    def __rtruediv__(self, other: OperandT) -> ResultT:
        """Right division: other / self."""
        from everybase.morphisms import DivOp

        return cast("ResultT", self._wrap_arithmetic_result(DivOp(other, self)))

    def __floordiv__(self, other: OperandT) -> ResultT:
        """Floor division: self // other."""
        from everybase.morphisms import FloorDivOp

        return cast("ResultT", self._wrap_arithmetic_result(FloorDivOp(self, other)))

    def __rfloordiv__(self, other: OperandT) -> ResultT:
        """Right floor division: other // self."""
        from everybase.morphisms import FloorDivOp

        return cast("ResultT", self._wrap_arithmetic_result(FloorDivOp(other, self)))


class ModuloableBase[OperandT, ResultT]:
    """Base for values that support modulo operation."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __mod__(self, other: OperandT) -> ResultT:
        """Modulo: self % other."""
        from everybase.morphisms import ModOp

        return cast("ResultT", self._wrap_arithmetic_result(ModOp(self, other)))

    def __rmod__(self, other: OperandT) -> ResultT:
        """Right modulo: other % self."""
        from everybase.morphisms import ModOp

        return cast("ResultT", self._wrap_arithmetic_result(ModOp(other, self)))


class PowerableBase[OperandT, ResultT]:
    """Base for values that support exponentiation."""

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __pow__(self, other: OperandT) -> ResultT:
        """Power: self ** other."""
        from everybase.morphisms import PowOp

        return cast("ResultT", self._wrap_arithmetic_result(PowOp(self, other)))

    def __rpow__(self, other: OperandT) -> ResultT:
        """Right power: other ** self."""
        from everybase.morphisms import PowOp

        return cast("ResultT", self._wrap_arithmetic_result(PowOp(other, self)))


# =============================================================================
# COMBINED BASES
# =============================================================================


class AdditiveBase[OperandT, ResultT](
    AddableBase[OperandT, ResultT],
    SubtractableBase[OperandT, ResultT],
    NegatableBase[ResultT],
):
    """Combined base for additive operations: +, -, neg, pos, abs."""

    pass


class MultiplicativeBase[OperandT, ResultT](
    MultiplyableBase[OperandT, ResultT],
    DivisibleBase[OperandT, ResultT],
    ModuloableBase[OperandT, ResultT],
    PowerableBase[OperandT, ResultT],
):
    """Combined base for multiplicative operations: *, /, //, %, **."""

    pass


class NumericBase[OperandT, ResultT](
    AdditiveBase[OperandT, ResultT],
    MultiplicativeBase[OperandT, ResultT],
):
    """Full arithmetic: +, -, *, /, //, %, **, neg, pos, abs."""

    pass
