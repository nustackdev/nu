"""Fraction type for exact rational arithmetic.

Pattern:
    FractionType = TypeBase[Fraction] + ComparableBase + arithmetic operations
    FractionValue = ValueBase + FractionType (computed results)
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from everybase import Sentinel
from everybase.abc import (
    ComparableBase,
    FloatValue,
    IntValue,
    TupleValue,
    TypeBase,
    ValueBase,
)


if TYPE_CHECKING:
    from everybase import Term

    from .args import DecimalArg, FractionArg


__all__ = [
    "FractionType",
    "FractionValue",
]


class FractionType(
    ComparableBase["Fraction | int | float | FractionType"],
    TypeBase[Fraction | Sentinel],
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
        numerator: int | Term[int],
        denominator: int | Term[int] = 1,
    ) -> FractionValue:
        """Create a FractionValue from numerator and denominator."""
        from everybase.abc import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, numerator, denominator))

    @classmethod
    def from_str(cls, value: str | Term[str]) -> FractionValue:
        """Create a FractionValue from a string."""
        from everybase.abc import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, value))

    @classmethod
    def from_float(cls, value: float | Term[float]) -> FractionValue:
        """Create a FractionValue from a float."""
        from everybase.abc import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> FractionValue:
        """Create a FractionValue from a Decimal."""
        from everybase.abc import FuncCallOp

        return FractionValue(FuncCallOp(Fraction, value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def numerator(self) -> IntValue:
        """Get the numerator."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "numerator"))

    def denominator(self) -> IntValue:
        """Get the denominator."""
        from everybase.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "denominator"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: FractionArg | int | float) -> FractionValue:
        """Add fractions."""
        from everybase.abc import AddOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(AddOp(self, other))

    def __radd__(self, other: Fraction | int | float) -> FractionValue:
        """Right add."""
        from everybase.abc import AddOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(AddOp(other, self))

    def __sub__(self, other: FractionArg | int | float) -> FractionValue:
        """Subtract fractions."""
        from everybase.abc import SubOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(SubOp(self, other))

    def __rsub__(self, other: Fraction | int | float) -> FractionValue:
        """Right subtract."""
        from everybase.abc import SubOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(SubOp(other, self))

    def __mul__(self, other: FractionArg | int | float) -> FractionValue:
        """Multiply fractions."""
        from everybase.abc import MulOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(MulOp(self, other))

    def __rmul__(self, other: Fraction | int | float) -> FractionValue:
        """Right multiply."""
        from everybase.abc import MulOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(MulOp(other, self))

    def __truediv__(self, other: FractionArg | int | float) -> FractionValue:
        """Divide fractions."""
        from everybase.abc import DivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(DivOp(self, other))

    def __rtruediv__(self, other: Fraction | int | float) -> FractionValue:
        """Right divide."""
        from everybase.abc import DivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(DivOp(other, self))

    def __floordiv__(self, other: FractionArg | int | float) -> IntValue:
        """Floor divide fractions."""
        from everybase.abc import FloorDivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return IntValue(FloorDivOp(self, other))

    def __mod__(self, other: FractionArg | int | float) -> FractionValue:
        """Modulo operation."""
        from everybase.abc import ModOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(ModOp(self, other))

    def __rfloordiv__(self, other: Fraction | int | float) -> IntValue:
        """Right floor divide."""
        from everybase.abc import FloorDivOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return IntValue(FloorDivOp(other, self))

    def __rmod__(self, other: Fraction | int | float) -> FractionValue:
        """Right modulo."""
        from everybase.abc import ModOp

        if isinstance(other, Fraction):
            other = FractionValue(other)
        return FractionValue(ModOp(other, self))

    def __pow__(self, other: int) -> FractionValue:
        """Raise to power."""
        from everybase.abc import PowOp

        return FractionValue(PowOp(self, other))

    def __neg__(self) -> FractionValue:
        """Negate."""
        from everybase.abc import NegOp

        return FractionValue(NegOp(self))

    def __abs__(self) -> FractionValue:
        """Absolute value."""
        from everybase.abc import AbsOp

        return FractionValue(AbsOp(self))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def limit_denominator(self, max_denominator: int = 10**6) -> FractionValue:
        """Find closest fraction with denominator at most max_denominator."""
        from everybase.abc import MethodCallOp

        return FractionValue(MethodCallOp(self, "limit_denominator", max_denominator))

    def as_float(self) -> FloatValue:
        """Convert to float."""
        from everybase.abc import FuncCallOp

        return FloatValue(FuncCallOp(float, self))

    def as_integer_ratio(self) -> TupleValue:
        """Return (numerator, denominator) tuple."""
        from everybase.abc import MethodCallOp

        return TupleValue(MethodCallOp(self, "as_integer_ratio"))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class FractionValue(ValueBase, FractionType):
    """Computed Fraction value (Python memory substrate)."""

    pass
