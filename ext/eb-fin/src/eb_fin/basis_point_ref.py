"""BasisPoint type for financial rate/fee representation.

Pattern:
    BasisPointType = Object[BasisPoint] + ComparableBase + arithmetic operations
    BasisPointValue = ValueBase + BasisPointType (computed results)

Basis point = 1/100th of a percent (500 bps = 5%).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Sentinel
from everybase.abc import (
    ComparableBase,
    FloatValue,
    IntValue,
    Object,
    ValueBase,
)

from .basis_point_cls import BasisPoint


if TYPE_CHECKING:
    from everybase import Term

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
    def from_int(cls, value: int | Term[int]) -> BasisPointValue:
        """Create from raw basis points."""
        from everybase.abc import FuncCallOp

        return BasisPointValue(FuncCallOp(BasisPoint, value))

    @classmethod
    def from_pct(cls, pct: float | Term[float]) -> BasisPointValue:
        """Create from percentage."""
        from everybase.abc import FuncCallOp

        return BasisPointValue(FuncCallOp(BasisPoint.from_pct, pct))

    @classmethod
    def from_dec(cls, dec: float | Term[float]) -> BasisPointValue:
        """Create from decimal."""
        from everybase.abc import FuncCallOp

        return BasisPointValue(FuncCallOp(BasisPoint.from_dec, dec))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> FloatValue:
        """Convert to percentage."""
        from everybase.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "to_pct"))

    def to_dec(self) -> FloatValue:
        """Convert to decimal."""
        from everybase.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "to_dec"))

    def to_int(self) -> IntValue:
        """Get raw basis points."""
        from everybase.abc import MethodCallOp

        return IntValue(MethodCallOp(self, "to_int"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Term) -> FloatValue:
        """Apply basis points to amount."""
        from everybase.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "apply", amount))

    def add_to(self, amount: int | float | Term) -> FloatValue:
        """Add basis points to amount."""
        from everybase.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: int | float | Term) -> FloatValue:
        """Subtract basis points from amount."""
        from everybase.abc import MethodCallOp

        return FloatValue(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: BasisPointArg) -> BasisPointValue:
        """Add basis points."""
        from everybase.abc import AddOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(AddOp(self, other))

    def __radd__(self, other: BasisPoint | int) -> BasisPointValue:
        """Right add."""
        from everybase.abc import AddOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(AddOp(other, self))

    def __sub__(self, other: BasisPointArg) -> BasisPointValue:
        """Subtract basis points."""
        from everybase.abc import SubOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(SubOp(self, other))

    def __rsub__(self, other: BasisPoint | int) -> BasisPointValue:
        """Right subtract."""
        from everybase.abc import SubOp

        if isinstance(other, BasisPoint):
            other = BasisPointValue(other)
        return BasisPointValue(SubOp(other, self))

    def __mul__(self, factor: int | float | Term) -> BasisPointValue:
        """Multiply by factor."""
        from everybase.abc import MulOp

        return BasisPointValue(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> BasisPointValue:
        """Right multiply."""
        from everybase.abc import MulOp

        return BasisPointValue(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | Term) -> BasisPointValue:
        """Divide by factor."""
        from everybase.abc import DivOp

        return BasisPointValue(DivOp(self, divisor))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class BasisPointValue(ValueBase, BasisPointType):
    """Computed BasisPoint value (Python memory substrate)."""

    pass
