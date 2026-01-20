"""Fraction Type."""

from __future__ import annotations

from fractions import Fraction

from term.ops import (
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
from term.types import (
    BaseType,
    ComparisonBase,
    FloatType,
    IntType,
    NegatableBase,
    TupleType,
)
from term.typing import Sentinel

from every._abc import FloatArg, IntArg, StrArg, Term
from everybase.type.decimal import DecimalArg

from .args import FractionArg


__all__ = [
    "FractionType",
]


class FractionType(
    ComparisonBase["Fraction | int | float | FractionType"],
    NegatableBase["FractionType"],
    BaseType[Fraction | Sentinel],
):
    """Term representing a Fraction.

    Provides exact rational arithmetic. Stored as "numerator/denominator"
    string for serialization.

    Example:
        >>> f = FractionType.from_components(3, 4)
        >>> f + FractionType.from_components(1, 2)  # Exact: 5/4
        >>> f.numerator()  # IntType: 3
        >>> f.denominator()  # IntType: 4
    """

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        return FractionType(operand)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        numerator: IntArg,
        denominator: IntArg = 1,
    ) -> FractionType:
        """Create a FractionType from numerator and denominator.

        Args:
            numerator: The numerator.
            denominator: The denominator (default 1).

        Returns:
            FractionType from components.

        Example:
            >>> FractionType.from_components(3, 4)  # 3/4
            >>> FractionType.from_components(5)  # 5/1
        """
        return cls(FuncCallOp(Fraction, numerator, denominator))

    @classmethod
    def from_str(cls, value: StrArg) -> FractionType:
        """Create a FractionType from a string.

        Args:
            value: String representation (e.g., "3/4", "0.75", "3").

        Returns:
            FractionType from string.

        Example:
            >>> FractionType.from_str("3/4")
            >>> FractionType.from_str("0.75")
        """
        return cls(FuncCallOp(Fraction, value))

    @classmethod
    def from_float(cls, value: FloatArg) -> FractionType:
        """Create a FractionType from a float.

        Args:
            value: Float value.

        Returns:
            FractionType representing the exact float.

        Example:
            >>> FractionType.from_float(0.5)  # 1/2
        """
        return cls(FuncCallOp(Fraction, value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> FractionType:
        """Create a FractionType from a Decimal.

        Args:
            value: Decimal value.

        Returns:
            FractionType from Decimal.
        """
        return cls(FuncCallOp(Fraction, value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def numerator(self) -> IntType:
        """Get the numerator.

        Returns:
            IntType containing the numerator.
        """
        return IntType(FuncCallOp(getattr, self, "numerator"))

    def denominator(self) -> IntType:
        """Get the denominator.

        Returns:
            IntType containing the denominator.
        """
        return IntType(FuncCallOp(getattr, self, "denominator"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Add fractions.

        Args:
            other: Value to add.

        Returns:
            Sum as FractionType.
        """
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(AddOp(self, other))

    def __radd__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Right add."""
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(AddOp(other, self))

    def __sub__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Subtract fractions.

        Args:
            other: Value to subtract.

        Returns:
            Difference as FractionType.
        """
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(SubOp(self, other))

    def __rsub__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Right subtract."""
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(SubOp(other, self))

    def __mul__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Multiply fractions.

        Args:
            other: Value to multiply.

        Returns:
            Product as FractionType.
        """
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(MulOp(self, other))

    def __rmul__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Right multiply."""
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(MulOp(other, self))

    def __truediv__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Divide fractions.

        Args:
            other: Divisor.

        Returns:
            Quotient as FractionType.
        """
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(DivOp(self, other))

    def __rtruediv__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Right divide."""
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(DivOp(other, self))

    def __floordiv__(self, other: FractionArg | IntArg | FloatArg) -> IntType:
        """Floor divide fractions.

        Args:
            other: Divisor.

        Returns:
            Floor quotient as IntType.
        """
        if isinstance(other, Fraction):
            other = FractionType(other)
        return IntType(FloorDivOp(self, other))

    def __rfloordiv__(self, other: FractionArg | IntArg | FloatArg) -> IntType:
        """Right floor divide."""
        if isinstance(other, Fraction):
            other = FractionType(other)
        return IntType(FloorDivOp(other, self))

    def __mod__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Modulo operation.

        Args:
            other: Divisor.

        Returns:
            Remainder as FractionType.
        """
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(ModOp(self, other))

    def __rmod__(self, other: FractionArg | IntArg | FloatArg) -> FractionType:
        """Right modulo."""
        if isinstance(other, Fraction):
            other = FractionType(other)
        return FractionType(ModOp(other, self))

    def __pow__(self, other: IntArg) -> FractionType:
        """Raise to power.

        Args:
            other: Integer exponent.

        Returns:
            Result as FractionType.
        """
        return FractionType(PowOp(self, other))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def limit_denominator(self, max_denominator: int = 10**6) -> FractionType:
        """Find closest fraction with denominator at most max_denominator.

        Args:
            max_denominator: Maximum allowed denominator.

        Returns:
            Closest FractionType with limited denominator.
        """
        return FractionType(MethodCallOp(self, "limit_denominator", max_denominator))

    def as_float(self) -> FloatType:
        """Convert to float.

        Returns:
            FloatType approximation.
        """
        return FloatType(FuncCallOp(float, self))

    def as_integer_ratio(self) -> TupleType:
        """Get as (numerator, denominator) tuple.

        Returns:
            TupleType with (numerator, denominator).
        """
        return TupleType(MethodCallOp(self, "as_integer_ratio"))
