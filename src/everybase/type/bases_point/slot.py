"""Basis Point slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import BasisPointRef


__all__ = [
    "BasisPointSlot",
]


class _BasisPointSlot(Slot):
    """Slot for BasisPoint values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = int

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> BasisPointRef:
        return BasisPointRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def BasisPointSlot() -> BasisPointRef:  # noqa: N802
    """Create slot for basis points.

    Stored as int for precision.

    Example:
        class Trade(Shape):
            slippage = BasisPointSlot()  # 500 = 5%
    """
    return _BasisPointSlot()  # type: ignore[return-value]
