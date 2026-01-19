"""Fraction Ref."""

from __future__ import annotations

from fractions import Fraction

from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef
from everyterm.ops import MethodCallOp
from everyterm.term import RValue

from .type import FractionType


__all__ = [
    "FractionRef",
]


class FractionRef(CollectionItemRefBase[Fraction, FractionType], PrimitiveRef):
    """Reference to a Fraction value in storage.

    Fraction values are stored as "numerator/denominator" strings.

    Example:
        class Recipe(Shape):
            cups_flour = FractionSlot()

        Recipe.cups_flour.set(Fraction(3, 4))
        Recipe.cups_flour.get()  # Returns FractionType
    """

    def set(self, value: Fraction | str | int | RValue) -> FractionType:
        """Set the Fraction value.

        Args:
            value: Fraction, string, or integer to store.

        Returns:
            FractionType representing the set operation result.
        """
        if isinstance(value, Fraction):
            val = str(value)
        elif isinstance(value, int):
            val = str(Fraction(value))
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return FractionType(TypedSetCmd(self, val))

    def get(self) -> FractionType:
        """Get the Fraction value.

        Returns:
            FractionType from storage.
        """
        return FractionType.from_str(GetOp(self))
