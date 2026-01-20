"""Basis Point Ref."""

from __future__ import annotations

from every.ops import MethodCallOp
from every.types import FloatType

from every._abc import FloatArg, IntArg, Term
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .args import BasesPointArg
from .cls import BasisPoint
from .type import BasisPointType


__all__ = [
    "BasisPointRef",
]


class BasisPointRef(CollectionItemRefBase[int, BasisPointType], PrimitiveRef):
    """Reference to BasisPoint in storage."""

    def set(self, value: IntArg | FloatArg | BasesPointArg) -> BasisPointType:
        """Set basis points."""
        if isinstance(value, BasisPoint):
            val = value.value
        elif isinstance(value, (int, float)):
            val = value
        else:
            val = MethodCallOp(value, "to_int")

        return BasisPointType(TypedSetCmd(self, val))

    def get(self) -> BasisPointType:
        """Get basis points."""
        return BasisPointType.from_int(GetOp(self))

    # Convenience methods
    def to_pct(self) -> FloatType:
        """Convert to percentage."""
        return self.get().to_pct()

    def to_dec(self) -> FloatType:
        """Convert to decimal."""
        return self.get().to_dec()

    def apply(self, amount: int | float | Term) -> FloatType:
        """Apply to amount."""
        return self.get().apply(amount)
