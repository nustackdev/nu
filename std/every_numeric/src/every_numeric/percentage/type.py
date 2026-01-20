"""Percentage Type."""

from __future__ import annotations

from term.ops import AddOp, DivOp, FuncCallOp, MethodCallOp, MulOp, SubOp
from term.types import BaseType, BoolType, ComparisonBase, FloatType, IntType
from term.typing import Sentinel

from every._abc import FloatArg, IntArg

from .args import PercentageArg
from .cls import Percentage


__all__ = [
    "PercentageType",
]


class PercentageType(
    ComparisonBase["Percentage | float | PercentageType"],
    BaseType[Percentage | Sentinel],
):
    """Type wrapping Percentage."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_float(cls, value: FloatArg) -> PercentageType:
        """Create from percentage float."""
        return cls(FuncCallOp(Percentage, value))

    @classmethod
    def from_dec(cls, dec: FloatArg) -> PercentageType:
        """Create from decimal."""
        return cls(FuncCallOp(Percentage.from_dec, dec))

    @classmethod
    def from_bps(cls, bps: IntArg) -> PercentageType:
        """Create from basis points."""
        return cls(FuncCallOp(Percentage.from_bps, bps))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_dec(self) -> FloatType:
        """Convert to decimal."""
        return FloatType(MethodCallOp(self, "to_dec"))

    def to_bps(self) -> IntType:
        """Convert to basis points."""
        return IntType(MethodCallOp(self, "to_bps"))

    def to_float(self) -> FloatType:
        """Get raw percentage."""
        return FloatType(MethodCallOp(self, "to_float"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: IntArg | FloatArg) -> FloatType:
        """Apply percentage to amount."""
        return FloatType(MethodCallOp(self, "apply", amount))

    def of(self, amount: IntArg | FloatArg) -> FloatType:
        """Alias for apply."""
        return FloatType(MethodCallOp(self, "of", amount))

    def add_to(self, amount: IntArg | FloatArg) -> FloatType:
        """Add percentage to amount."""
        return FloatType(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: IntArg | FloatArg) -> FloatType:
        """Subtract percentage from amount."""
        return FloatType(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> BoolType:
        """Check if within range."""
        return BoolType(MethodCallOp(self, "is_valid", min_val, max_val))

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> PercentageType:
        """Clamp to range."""
        return PercentageType(MethodCallOp(self, "clamp", min_val, max_val))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: PercentageArg | FloatArg) -> PercentageType:
        """Add percentages."""
        if isinstance(other, Percentage):
            other = PercentageType(other)
        return PercentageType(AddOp(self, other))

    def __sub__(self, other: PercentageArg | FloatArg) -> PercentageType:
        """Subtract percentages."""
        if isinstance(other, Percentage):
            other = PercentageType(other)
        return PercentageType(SubOp(self, other))

    def __mul__(self, factor: IntArg | FloatArg) -> PercentageType:
        """Multiply by factor."""
        return PercentageType(MulOp(self, factor))

    def __truediv__(self, divisor: IntArg | FloatArg) -> PercentageType:
        """Divide by factor."""
        return PercentageType(DivOp(self, divisor))
