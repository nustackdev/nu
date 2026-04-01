"""Percentage type for percentage values.

Pattern:
    PercentageType = Object[Percentage] + ComparableBase + arithmetic operations
    PercentageValue = Interface + PercentageType (computed results)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    BoolI,
    ComparableBase,
    FloatI,
    IntI,
    Object,
    Interface,
)

from .percentage_cls import Percentage


if TYPE_CHECKING:
    from nu import Nu

    from .args import PercentageArg


__all__ = [
    "PercentageType",
    "PercentageValue",
]


class PercentageType(
    ComparableBase["Percentage | float | PercentageType"],
    Object[Percentage | Sentinel],
):
    """Abstract type for Percentage operations.

    Provides percentage operations.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> PercentageValue:
        """Create from percentage float."""
        from nu import FuncCallOp

        return PercentageValue(FuncCallOp(Percentage, value))

    @classmethod
    def from_dec(cls, dec: float | Nu[float]) -> PercentageValue:
        """Create from decimal."""
        from nu import FuncCallOp

        return PercentageValue(FuncCallOp(Percentage.from_dec, dec))

    @classmethod
    def from_bps(cls, bps: int | Nu[int]) -> PercentageValue:
        """Create from basis points."""
        from nu import FuncCallOp

        return PercentageValue(FuncCallOp(Percentage.from_bps, bps))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_dec(self) -> FloatI:
        """Convert to decimal."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "to_dec"))

    def to_bps(self) -> IntI:
        """Convert to basis points."""
        from nu import MethodCallOp

        return IntI(MethodCallOp(self, "to_bps"))

    def to_float(self) -> FloatI:
        """Get raw percentage."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "to_float"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Nu) -> FloatI:
        """Apply percentage to amount."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "apply", amount))

    def of(self, amount: int | float | Nu) -> FloatI:
        """Alias for apply."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "of", amount))

    def add_to(self, amount: int | float | Nu) -> FloatI:
        """Add percentage to amount."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: int | float | Nu) -> FloatI:
        """Subtract percentage from amount."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> BoolI:
        """Check if within range."""
        from nu import MethodCallOp

        return BoolI(MethodCallOp(self, "is_valid", min_val, max_val))

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> PercentageValue:
        """Clamp to range."""
        from nu import MethodCallOp

        return PercentageValue(MethodCallOp(self, "clamp", min_val, max_val))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: PercentageArg | float) -> PercentageValue:
        """Add percentages."""
        from nu import AddOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(AddOp(self, other))

    def __radd__(self, other: Percentage | float) -> PercentageValue:
        """Right add."""
        from nu import AddOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(AddOp(other, self))

    def __sub__(self, other: PercentageArg | float) -> PercentageValue:
        """Subtract percentages."""
        from nu import SubOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(SubOp(self, other))

    def __rsub__(self, other: Percentage | float) -> PercentageValue:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(SubOp(other, self))

    def __mul__(self, factor: int | float | Nu) -> PercentageValue:
        """Multiply by factor."""
        from nu import MulOp

        return PercentageValue(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> PercentageValue:
        """Right multiply."""
        from nu import MulOp

        return PercentageValue(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | Nu) -> PercentageValue:
        """Divide by factor."""
        from nu import DivOp

        return PercentageValue(DivOp(self, divisor))

    def __neg__(self) -> PercentageValue:
        """Negate."""
        from nu import NegOp

        return PercentageValue(NegOp(self))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class PercentageValue(Interface, PercentageType):
    """Computed Percentage value (Python memory substrate)."""

    pass
