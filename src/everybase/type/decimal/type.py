"""Decimal Type."""

from __future__ import annotations

from decimal import Decimal

from everyterm.ops import (
    AddOp,
    DivOp,
    FloorDivOp,
    FuncCallOp,
    MethodCallOp,
    ModOp,
    MulOp,
    PowOp,
    SubOp,
)
from everyterm.term import FloatArg, IntArg, StrArg, Term
from everyterm.types import BaseType, BoolType, ComparisonBase, IntType, NegatableBase
from everyterm.typing import Sentinel

from .args import DecimalArg


__all__ = [
    "DecimalType",
]


class DecimalType(
    ComparisonBase["Decimal | int | float | str | DecimalType"],
    NegatableBase["DecimalType"],
    BaseType[Decimal | Sentinel],
):
    """Type representing a Decimal.

    Provides arbitrary precision decimal arithmetic for financial
    and scientific calculations where floating point errors are unacceptable.
    Stored as string for exact representation.

    Example:
        >>> d = DecimalType.from_str("123.456")
        >>> d + DecimalType.from_str("0.001")  # Exact
        >>> d.quantize("0.01")  # Round to 2 decimal places
    """

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        return DecimalType(operand)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: StrArg) -> DecimalType:
        """Create a DecimalType from a string."""
        return cls(FuncCallOp(Decimal, value))

    @classmethod
    def from_int(cls, value: IntArg) -> DecimalType:
        """Create a DecimalType from an integer."""
        return cls(FuncCallOp(Decimal, value))

    @classmethod
    def from_float(cls, value: FloatArg) -> DecimalType:
        """Create a DecimalType from a float.

        Note: Converting from float may introduce precision issues.
        Prefer from_str() for exact values.
        """
        return cls(FuncCallOp(Decimal, value))

    @classmethod
    def from_tuple(
        cls,
        sign: IntArg,
        digits: tuple[int, ...],
        exponent: IntArg,
    ) -> DecimalType:
        """Create a DecimalType from sign, digits, and exponent."""
        return cls(FuncCallOp(Decimal, (sign, digits, exponent)))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: DecimalArg) -> DecimalType:
        """Add two decimals."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(AddOp(self, other))

    def __radd__(self, other: DecimalArg | IntArg | FloatArg | StrArg) -> DecimalType:
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(AddOp(other, self))

    def __sub__(self, other: DecimalArg) -> DecimalType:
        """Subtract decimals."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(SubOp(self, other))

    def __rsub__(self, other: DecimalArg | IntArg | FloatArg | StrArg) -> DecimalType:
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(SubOp(other, self))

    def __mul__(self, other: DecimalArg) -> DecimalType:
        """Multiply decimals."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(MulOp(self, other))

    def __rmul__(self, other: DecimalArg | IntArg | FloatArg | StrArg) -> DecimalType:
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(MulOp(other, self))

    def __truediv__(self, other: DecimalArg) -> DecimalType:
        """Divide decimals."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(DivOp(self, other))

    def __rtruediv__(self, other: DecimalArg | IntArg | FloatArg | StrArg) -> DecimalType:
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(DivOp(other, self))

    def __floordiv__(self, other: DecimalArg) -> DecimalType:
        """Floor divide decimals."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(FloorDivOp(self, other))

    def __rfloordiv__(self, other: DecimalArg | IntArg | FloatArg | StrArg) -> DecimalType:
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(FloorDivOp(other, self))

    def __mod__(self, other: DecimalArg) -> DecimalType:
        """Modulo operation."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(ModOp(self, other))

    def __rmod__(self, other: DecimalArg | IntArg | FloatArg | StrArg) -> DecimalType:
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(ModOp(other, self))

    def __pow__(self, other: IntArg | DecimalArg) -> DecimalType:
        """Raise to power."""
        if isinstance(other, Decimal):
            other = DecimalType(other)
        return DecimalType(PowOp(self, other))

    # =========================================================================
    # ROUNDING AND QUANTIZATION
    # =========================================================================

    def quantize(self, exp: StrArg | DecimalArg, rounding: StrArg | None = None) -> DecimalType:
        """Quantize to a given exponent (e.g., "0.01" for 2 decimal places)."""
        if isinstance(exp, Decimal):
            exp = DecimalType(exp)
        if rounding is not None:
            return DecimalType(MethodCallOp(self, "quantize", exp, rounding))
        return DecimalType(MethodCallOp(self, "quantize", exp))

    def normalize(self) -> DecimalType:
        """Remove trailing zeros."""
        return DecimalType(MethodCallOp(self, "normalize"))

    def sqrt(self) -> DecimalType:
        """Square root."""
        return DecimalType(MethodCallOp(self, "sqrt"))

    def exp(self) -> DecimalType:
        """Exponential (e^self)."""
        return DecimalType(MethodCallOp(self, "exp"))

    def ln(self) -> DecimalType:
        """Natural logarithm."""
        return DecimalType(MethodCallOp(self, "ln"))

    def log10(self) -> DecimalType:
        """Base-10 logarithm."""
        return DecimalType(MethodCallOp(self, "log10"))

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def is_finite(self) -> BoolType:
        """Check if value is finite."""
        return BoolType(MethodCallOp(self, "is_finite"))

    def is_infinite(self) -> BoolType:
        """Check if value is infinite."""
        return BoolType(MethodCallOp(self, "is_infinite"))

    def is_signed(self) -> BoolType:
        """Check if value is negative."""
        return BoolType(MethodCallOp(self, "is_signed"))

    def is_zero(self) -> BoolType:
        """Check if value is zero."""
        return BoolType(MethodCallOp(self, "is_zero"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntType:
        """Convert to integer (truncating decimal)."""
        return IntType(FuncCallOp(int, self))
