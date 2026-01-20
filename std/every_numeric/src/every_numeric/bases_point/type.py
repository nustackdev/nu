"""Basis Point Type."""

from __future__ import annotations

from every._abc import FloatArg, IntArg, Sentinel
from every._base import BaseType, ComparisonBase
from every.ops import AddOp, DivOp, FuncCallOp, MethodCallOp, MulOp, SubOp
from every.types import FloatType, IntType

from .args import BasesPointArg
from .cls import BasisPoint


__all__ = [
    "BasisPointType",
]


class BasisPointType(
    ComparisonBase["BasisPoint | int | BasisPointType"],
    BaseType[BasisPoint | Sentinel],
):
    """Type wrapping BasisPoint.

    Example:
        >>> bps = BasisPointType.from_int(500)
        >>> bps.to_pct()  # FloatType(5.0)
        >>> bps.apply(1000)  # FloatType(50.0)
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_int(cls, value: IntArg) -> BasisPointType:
        """Create from raw basis points."""
        return cls(FuncCallOp(BasisPoint, value))

    @classmethod
    def from_pct(cls, pct: FloatArg) -> BasisPointType:
        """Create from percentage."""
        return cls(FuncCallOp(BasisPoint.from_pct, pct))

    @classmethod
    def from_dec(cls, dec: FloatArg) -> BasisPointType:
        """Create from decimal."""
        return cls(FuncCallOp(BasisPoint.from_dec, dec))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> FloatType:
        """Convert to percentage."""
        return FloatType(MethodCallOp(self, "to_pct"))

    def to_dec(self) -> FloatType:
        """Convert to decimal."""
        return FloatType(MethodCallOp(self, "to_dec"))

    def to_int(self) -> IntType:
        """Get raw basis points."""
        return IntType(MethodCallOp(self, "to_int"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: IntArg | FloatArg) -> FloatType:
        """Apply basis points to amount."""
        return FloatType(MethodCallOp(self, "apply", amount))

    def add_to(self, amount: IntArg | FloatArg) -> FloatType:
        """Add basis points to amount."""
        return FloatType(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: IntArg | FloatArg) -> FloatType:
        """Subtract basis points from amount."""
        return FloatType(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: IntArg | FloatArg | BasesPointArg) -> BasisPointType:
        """Add basis points."""
        if isinstance(other, BasisPoint):
            other = BasisPointType(other)
        return BasisPointType(AddOp(self, other))

    def __sub__(self, other: IntArg | FloatArg | BasesPointArg) -> BasisPointType:
        """Subtract basis points."""
        if isinstance(other, BasisPoint):
            other = BasisPointType(other)
        return BasisPointType(SubOp(self, other))

    def __mul__(self, factor: IntArg | FloatArg | BasesPointArg) -> BasisPointType:
        """Multiply by factor."""
        if isinstance(factor, BasisPoint):
            factor = BasisPointType(factor)
        return BasisPointType(MulOp(self, factor))

    def __truediv__(self, divisor: IntArg | FloatArg | BasesPointArg) -> BasisPointType:
        """Divide by factor."""
        if isinstance(divisor, BasisPoint):
            divisor = BasisPointType(divisor)
        return BasisPointType(DivOp(self, divisor))
