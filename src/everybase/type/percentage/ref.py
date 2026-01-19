"""Percentage Ref."""

from __future__ import annotations

from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef
from everyterm.ops import MethodCallOp
from everyterm.term import FloatArg, IntArg
from everyterm.types import BoolType, FloatType, IntType

from .args import PercentageArg
from .cls import Percentage
from .type import PercentageType


__all__ = [
    "PercentageRef",
]


class PercentageRef(CollectionItemRefBase[float, PercentageType], PrimitiveRef):
    """Reference to Percentage in storage."""

    def set(self, value: PercentageArg | FloatArg) -> PercentageType:
        """Set percentage."""
        if isinstance(value, Percentage):
            val = value.value
        elif isinstance(value, (int, float)):
            val = value
        else:
            val = MethodCallOp(value, "to_float") if isinstance(value, PercentageType) else value
        return PercentageType(TypedSetCmd(self, val))

    def get(self) -> PercentageType:
        """Get percentage."""
        return PercentageType.from_float(GetOp(self))

    # Convenience methods
    def to_dec(self) -> FloatType:
        """Convert to decimal."""
        return self.get().to_dec()

    def to_bps(self) -> IntType:
        """Convert to basis points."""
        return self.get().to_bps()

    def apply(self, amount: IntArg | FloatArg) -> FloatType:
        """Apply to amount."""
        return self.get().apply(amount)

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> BoolType:
        """Check if within range."""
        return self.get().is_valid(min_val, max_val)
