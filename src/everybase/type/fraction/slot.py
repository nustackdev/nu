"""Fraction slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import FractionRef


__all__ = [
    "FractionSlot",
]


class _FractionSlot(Slot):
    """Slot implementation for Fraction values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = str  # Stored as "numerator/denominator"

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> FractionRef:
        """Create FractionRef for this slot."""
        return FractionRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def FractionSlot() -> FractionRef:  # noqa: N802
    """Create a slot for Fraction values.

    Fractions are stored as "numerator/denominator" strings and
    automatically converted to/from Python Fraction objects.
    Use this for exact rational arithmetic.

    Returns:
        FractionRef slot.

    Example:
        class Recipe(Shape):
            cups_flour = FractionSlot()
            cups_sugar = FractionSlot()
    """
    return _FractionSlot()  # type: ignore[return-value]
