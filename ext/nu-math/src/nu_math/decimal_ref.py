"""Decimal type for arbitrary precision decimal arithmetic.

Pattern:
    DecimalType = Object[Decimal] + ComparableBase + arithmetic operations
    DecimalValue = ValueBase + DecimalType (computed results)
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    BoolValue,
    ComparableBase,
    IntValue,
    Object,
    ValueBase,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import DecimalArg


__all__ = [
    "DecimalType",
    "DecimalValue",
]


class DecimalType(
    ComparableBase["Decimal | int | float | str | DecimalType"],
    Object[Decimal | Sentinel],
):
    """Abstract type for Decimal operations.

    Provides arbitrary precision decimal arithmetic for financial
    and scientific calculations where floating point errors are unacceptable.

    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS (class methods returning DecimalValue)
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> DecimalValue:
        """Create a DecimalValue from a string."""
        from nu import FuncCallOp

        return DecimalValue(FuncCallOp(Decimal, value))

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> DecimalValue:
        """Create a DecimalValue from an integer."""
        from nu import FuncCallOp

        return DecimalValue(FuncCallOp(Decimal, value))

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> DecimalValue:
        """Create a DecimalValue from a float.

        Note: Converting from float may introduce precision issues.
        Prefer from_str() for exact values.
        """
        from nu import FuncCallOp

        return DecimalValue(FuncCallOp(Decimal, value))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: DecimalArg) -> DecimalValue:
        """Add two decimals."""
        from nu import AddOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(AddOp(self, other))

    def __radd__(self, other: Decimal | int | float | str) -> DecimalValue:
        """Right add."""
        from nu import AddOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(AddOp(other, self))

    def __sub__(self, other: DecimalArg) -> DecimalValue:
        """Subtract decimals."""
        from nu import SubOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(SubOp(self, other))

    def __rsub__(self, other: Decimal | int | float | str) -> DecimalValue:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(SubOp(other, self))

    def __mul__(self, other: DecimalArg) -> DecimalValue:
        """Multiply decimals."""
        from nu import MulOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(MulOp(self, other))

    def __rmul__(self, other: Decimal | int | float | str) -> DecimalValue:
        """Right multiply."""
        from nu import MulOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(MulOp(other, self))

    def __truediv__(self, other: DecimalArg) -> DecimalValue:
        """Divide decimals."""
        from nu import DivOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(DivOp(self, other))

    def __rtruediv__(self, other: Decimal | int | float | str) -> DecimalValue:
        """Right divide."""
        from nu import DivOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(DivOp(other, self))

    def __floordiv__(self, other: DecimalArg) -> DecimalValue:
        """Floor divide decimals."""
        from nu import FloorDivOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(FloorDivOp(self, other))

    def __mod__(self, other: DecimalArg) -> DecimalValue:
        """Modulo operation."""
        from nu import ModOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(ModOp(self, other))

    def __pow__(self, other: int | DecimalArg) -> DecimalValue:
        """Raise to power."""
        from nu import PowOp

        if isinstance(other, Decimal):
            other = DecimalValue(other)
        return DecimalValue(PowOp(self, other))

    def __neg__(self) -> DecimalValue:
        """Negate."""
        from nu import NegOp

        return DecimalValue(NegOp(self))

    def __abs__(self) -> DecimalValue:
        """Absolute value."""
        from nu import AbsOp

        return DecimalValue(AbsOp(self))

    # =========================================================================
    # ROUNDING AND QUANTIZATION
    # =========================================================================

    def quantize(self, exp: str | DecimalArg, rounding: str | None = None) -> DecimalValue:
        """Quantize to a given exponent (e.g., "0.01" for 2 decimal places)."""
        from nu import MethodCallOp

        if isinstance(exp, Decimal):
            exp = DecimalValue(exp)
        if rounding is not None:
            return DecimalValue(MethodCallOp(self, "quantize", exp, rounding))
        return DecimalValue(MethodCallOp(self, "quantize", exp))

    def normalize(self) -> DecimalValue:
        """Remove trailing zeros."""
        from nu import MethodCallOp

        return DecimalValue(MethodCallOp(self, "normalize"))

    def sqrt(self) -> DecimalValue:
        """Square root."""
        from nu import MethodCallOp

        return DecimalValue(MethodCallOp(self, "sqrt"))

    def exp(self) -> DecimalValue:
        """Exponential (e^self)."""
        from nu import MethodCallOp

        return DecimalValue(MethodCallOp(self, "exp"))

    def ln(self) -> DecimalValue:
        """Natural logarithm."""
        from nu import MethodCallOp

        return DecimalValue(MethodCallOp(self, "ln"))

    def log10(self) -> DecimalValue:
        """Base-10 logarithm."""
        from nu import MethodCallOp

        return DecimalValue(MethodCallOp(self, "log10"))

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def is_finite(self) -> BoolValue:
        """Check if value is finite."""
        from nu import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_finite"))

    def is_infinite(self) -> BoolValue:
        """Check if value is infinite."""
        from nu import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_infinite"))

    def is_signed(self) -> BoolValue:
        """Check if value is negative."""
        from nu import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_signed"))

    def is_zero(self) -> BoolValue:
        """Check if value is zero."""
        from nu import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_zero"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntValue:
        """Convert to integer (truncating decimal)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(int, self))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class DecimalValue(ValueBase, DecimalType):
    """Computed Decimal value (Python memory substrate)."""

    pass
