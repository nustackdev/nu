"""BasisPoint type for financial rate/fee representation.

Pattern:
    BasisPointType = Object[BasisPoint] + ComparableBase + arithmetic operations
    BasisPointValue = Interface + BasisPointType (computed results)

Basis point = 1/100th of a percent (500 bps = 5%).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    ComparableBase,
    FloatI,
    IntI,
    Object,
    Interface,
)

from .basis_point_cls import BasisPoint


if TYPE_CHECKING:
    from nu import Nu

    from .args import BasisPointArg


__all__ = [
    "BasisPointType",
    "BasisPointValue",
]


class BasisPointType(
    ComparableBase["BasisPoint | int | BasisPointType"],
    Object[BasisPoint | Sentinel],
):
    """Abstract type for BasisPoint operations.

    Provides basis point operations for precise rate/fee representation.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> BasisPointValue:
        """Create from raw basis points."""
        from nu import FuncCallOp

        return BasisPointValue(FuncCallOp(BasisPoint, value))

    @classmethod
    def from_pct(cls, pct: float | Nu[float]) -> BasisPointValue:
        """Create from percentage."""
        from nu import FuncCallOp

        return BasisPointValue(FuncCallOp(BasisPoint.from_pct, pct))

    @classmethod
    def from_dec(cls, dec: float | Nu[float]) -> BasisPointValue:
        """Create from decimal."""
        from nu import FuncCallOp

        return BasisPointValue(FuncCallOp(BasisPoint.from_dec, dec))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> FloatI:
        """Convert to percentage."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "to_pct"))

    def to_dec(self) -> FloatI:
        """Convert to decimal."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "to_dec"))

    def to_int(self) -> IntI:
        """Get raw basis points."""
        from nu import MethodCallOp

        return IntI(MethodCallOp(self, "to_int"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Nu) -> FloatI:
        """Apply basis points to amount."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "apply", amount))

    def add_to(self, amount: int | float | Nu) -> FloatI:
        """Add basis points to amount."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: int | float | Nu) -> FloatI:
        """Subtract basis points from amount."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: BasisPointArg) -> BasisPointValue:
        """Add basis points."""
        from nu import AddOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(AddOp(self, other))

    def __radd__(self, other: BasisPoint | int) -> BasisPointValue:
        """Right add."""
        from nu import AddOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(AddOp(other, self))

    def __sub__(self, other: BasisPointArg) -> BasisPointValue:
        """Subtract basis points."""
        from nu import SubOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(SubOp(self, other))

    def __rsub__(self, other: BasisPoint | int) -> BasisPointValue:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(SubOp(other, self))

    def __mul__(self, factor: int | float | Nu) -> BasisPointValue:
        """Multiply by factor."""
        from nu import MulOp

        return BasisPointValue(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> BasisPointValue:
        """Right multiply."""
        from nu import MulOp

        return BasisPointValue(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | Nu) -> BasisPointValue:
        """Divide by factor."""
        from nu import DivOp

        return BasisPointValue(DivOp(self, divisor))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class BasisPointValue(Interface, BasisPointType):
    """Computed BasisPoint value (Python memory substrate)."""

    pass
