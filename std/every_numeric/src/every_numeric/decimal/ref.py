"""Decimal Ref."""

from __future__ import annotations

from decimal import Decimal

from term.ops import MethodCallOp
from term.types import BoolType, IntType

from every._abc import StrArg
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .args import DecimalArg
from .type import DecimalType


__all__ = [
    "DecimalRef",
]


class DecimalRef(CollectionItemRefBase[Decimal, DecimalType], PrimitiveRef):
    """Reference to a Decimal value in storage."""

    def set(self, value: DecimalArg) -> DecimalType:
        """Set the Decimal value."""
        if isinstance(value, Decimal):
            val = str(value)
        elif isinstance(value, (int, float)):
            val = str(Decimal(value))
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return DecimalType(TypedSetCmd(self, val))

    def get(self) -> DecimalType:
        """Get the Decimal value."""
        return DecimalType.from_str(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def quantize(self, exp: StrArg | DecimalArg, rounding: StrArg | None = None) -> DecimalType:
        return self.get().quantize(exp, rounding)

    def normalize(self) -> DecimalType:
        return self.get().normalize()

    def sqrt(self) -> DecimalType:
        return self.get().sqrt()

    def is_finite(self) -> BoolType:
        return self.get().is_finite()

    def is_signed(self) -> BoolType:
        return self.get().is_signed()

    def is_zero(self) -> BoolType:
        return self.get().is_zero()

    def to_int(self) -> IntType:
        return self.get().to_int()
