"""Fraction type for exact rational arithmetic.

Pattern:
    FractionType = Object[Fraction] + ComparableBase + arithmetic operations
    FractionValue = Interface + FractionType (computed results)
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    ComparableBase,
    FloatI,
    IntI,
    Object,
    TupleI,
    Interface,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import DecimalArg, FractionArg


__all__ = [
    "FractionType",
    "FractionValue",
]


class FractionType(
    ComparableBase["Fraction | int | float | FractionType"],
    Object[Fraction | Sentinel],
):
    """Abstract type for Fraction operations.

    Provides exact rational arithmetic. Uses *Type in arguments
    (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        numerator: int | Nu[int],
        denominator: int | Nu[int] = 1,
    ) -> FractionValue:
        """Create a FractionValue from numerator and denominator."""
        from nu import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, numerator, denominator))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> FractionValue:
        """Create a FractionValue from a string."""
        from nu import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, value))

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> FractionValue:
        """Create a FractionValue from a float."""
        from nu import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> FractionValue:
        """Create a FractionValue from a Decimal."""
        from nu import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def numerator(self) -> IntI:
        """Get the numerator."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "numerator"))

    def denominator(self) -> IntI:
        """Get the denominator."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "denominator"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: FractionArg | int | float) -> FractionValue:
        """Add fractions."""
        from nu import AddOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(AddOp(self, other))

    def __radd__(self, other: Fraction | int | float) -> FractionValue:
        """Right add."""
        from nu import AddOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(AddOp(other, self))

    def __sub__(self, other: FractionArg | int | float) -> FractionValue:
        """Subtract fractions."""
        from nu import SubOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(SubOp(self, other))

    def __rsub__(self, other: Fraction | int | float) -> FractionValue:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(SubOp(other, self))

    def __mul__(self, other: FractionArg | int | float) -> FractionValue:
        """Multiply fractions."""
        from nu import MulOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(MulOp(self, other))

    def __rmul__(self, other: Fraction | int | float) -> FractionValue:
        """Right multiply."""
        from nu import MulOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(MulOp(other, self))

    def __truediv__(self, other: FractionArg | int | float) -> FractionValue:
        """Divide fractions."""
        from nu import DivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(DivOp(self, other))

    def __rtruediv__(self, other: Fraction | int | float) -> FractionValue:
        """Right divide."""
        from nu import DivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(DivOp(other, self))

    def __floordiv__(self, other: FractionArg | int | float) -> IntI:
        """Floor divide fractions."""
        from nu import FloorDivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return IntI(FloorDivOp(self, other))

    def __mod__(self, other: FractionArg | int | float) -> FractionValue:
        """Modulo operation."""
        from nu import ModOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(ModOp(self, other))

    def __rfloordiv__(self, other: Fraction | int | float) -> IntI:
        """Right floor divide."""
        from nu import FloorDivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return IntI(FloorDivOp(other, self))

    def __rmod__(self, other: Fraction | int | float) -> FractionValue:
        """Right modulo."""
        from nu import ModOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(ModOp(other, self))

    def __pow__(self, other: int) -> FractionValue:
        """Raise to power."""
        from nu import PowOp

        return FractionValue(PowOp(self, other))

    def __neg__(self) -> FractionValue:
        """Negate."""
        from nu import NegOp

        return FractionValue(NegOp(self))

    def __abs__(self) -> FractionValue:
        """Absolute value."""
        from nu import AbsOp

        return FractionValue(AbsOp(self))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def limit_denominator(self, max_denominator: int = 10**6) -> FractionValue:
        """Find closest fraction with denominator at most max_denominator."""
        from nu import MethodCallOp

        return FractionValue(MethodCallOp(self, "limit_denominator", max_denominator))

    def as_float(self) -> FloatI:
        """Convert to float."""
        from nu import FuncCallOp

        return FloatI(FuncCallOp(float, self))

    def as_integer_ratio(self) -> TupleI:
        """Return (numerator, denominator) tuple."""
        from nu import MethodCallOp

        return TupleI(MethodCallOp(self, "as_integer_ratio"))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class FractionValue(Interface, FractionType):
    """Computed Fraction value (Python memory substrate)."""

    pass
