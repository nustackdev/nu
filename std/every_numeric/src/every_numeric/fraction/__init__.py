"""Fraction type for Shape system.

Provides FractionType, FractionRef, and FractionSlot for working with
Python Fraction objects. Perfect for exact rational arithmetic.

Example:
    from everybase.type import FractionSlot
    from fractions import Fraction

    class Recipe(Shape):
        cups_flour = FractionSlot()
        cups_sugar = FractionSlot()

    # Operations
    Recipe.cups_flour.set(Fraction(3, 4))
    Recipe.cups_flour.get() + Fraction(1, 2)
"""

from __future__ import annotations

from .args import FractionArg
from .ref import FractionRef
from .slot import FractionSlot
from .type import FractionType


__all__ = [
    "FractionType",
    "FractionRef",
    "FractionSlot",
    "FractionArg",
]
