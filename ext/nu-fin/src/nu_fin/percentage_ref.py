"""Percentage type for percentage values.

Pattern:
    PercentageType = Object[Percentage] + ComparableBase + arithmetic operations
    PercentageValue = ValueBase + PercentageType (computed results)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Sentinel
from nu.abc import (
    BoolValue,
    ComparableBase,
    FloatValue,
    IntValue,
    Object,
    ValueBase,
)

from .percentage_cls import Percentage


if TYPE_CHECKING:
    from nu import Term

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
    def from_float(cls, value: float | Term[float]) -> PercentageValue:
        """Create from percentage float."""
        from nu.abc import FuncCallOp

        return PercentageValue(FuncCallOp(Percentage, value))

    @classmethod
    def from_dec(cls, dec: float | Term[float]) -> PercentageValue:
        """Create from decimal."""
        from nu.abc import FuncCallOp

        return PercentageValue(FuncCallOp(Percentage.from_dec, dec))

    @classmethod
    def from_bps(cls, bps: int | Term[int]) -> PercentageValue:
        """Create from basis points."""
        from nu.abc import FuncCallOp

        return PercentageValue(FuncCallOp(Percentage.from_bps, bps))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_dec(self) -> FloatValue:
        """Convert to decimal."""
        from nu.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "to_dec"))

    def to_bps(self) -> IntValue:
        """Convert to basis points."""
        from nu.abc import MethodCallOp

        return IntValue(MethodCallOp(self, "to_bps"))

    def to_float(self) -> FloatValue:
        """Get raw percentage."""
        from nu.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "to_float"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Term) -> FloatValue:
        """Apply percentage to amount."""
        from nu.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "apply", amount))

    def of(self, amount: int | float | Term) -> FloatValue:
        """Alias for apply."""
        from nu.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "of", amount))

    def add_to(self, amount: int | float | Term) -> FloatValue:
        """Add percentage to amount."""
        from nu.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: int | float | Term) -> FloatValue:
        """Subtract percentage from amount."""
        from nu.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> BoolValue:
        """Check if within range."""
        from nu.abc import MethodCallOp

        return BoolValue(MethodCallOp(self, "is_valid", min_val, max_val))

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> PercentageValue:
        """Clamp to range."""
        from nu.abc import MethodCallOp

        return PercentageValue(MethodCallOp(self, "clamp", min_val, max_val))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: PercentageArg | float) -> PercentageValue:
        """Add percentages."""
        from nu.abc import AddOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(AddOp(self, other))

    def __radd__(self, other: Percentage | float) -> PercentageValue:
        """Right add."""
        from nu.abc import AddOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(AddOp(other, self))

    def __sub__(self, other: PercentageArg | float) -> PercentageValue:
        """Subtract percentages."""
        from nu.abc import SubOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(SubOp(self, other))

    def __rsub__(self, other: Percentage | float) -> PercentageValue:
        """Right subtract."""
        from nu.abc import SubOp

        if isinstance(other, Percentage):
            other = PercentageValue(other)
        return PercentageValue(SubOp(other, self))

    def __mul__(self, factor: int | float | Term) -> PercentageValue:
        """Multiply by factor."""
        from nu.abc import MulOp

        return PercentageValue(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> PercentageValue:
        """Right multiply."""
        from nu.abc import MulOp

        return PercentageValue(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | Term) -> PercentageValue:
        """Divide by factor."""
        from nu.abc import DivOp

        return PercentageValue(DivOp(self, divisor))

    def __neg__(self) -> PercentageValue:
        """Negate."""
        from nu.abc import NegOp

        return PercentageValue(NegOp(self))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class PercentageValue(ValueBase, PercentageType):
    """Computed Percentage value (Python memory substrate)."""

    pass
