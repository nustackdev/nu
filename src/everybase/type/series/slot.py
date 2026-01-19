"""Series slot."""

from __future__ import annotations

from everyterm.shape import Shape, Slot
from everyterm.term import Ref

from .ref import SeriesRef


__all__ = [
    "SeriesSlot",
]


class _SeriesSlot(Slot):
    """Slot for Series values."""

    def __init__(self) -> None:
        super().__init__()
        self.value_type = list

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> SeriesRef:
        return SeriesRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def SeriesSlot() -> SeriesRef:  # noqa: N802
    """Create slot for time series data.

    Stored as list of dicts, provides rich calculations.

    Example:
        class PriceHistory(Shape):
            prices = SeriesSlot()

        # Access
        PriceHistory.prices.sma(20)
        PriceHistory.prices.rsi(14)
    """
    return _SeriesSlot()  # type: ignore[return-value]
