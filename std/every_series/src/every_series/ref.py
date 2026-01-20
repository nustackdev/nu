"""Series Ref."""

from __future__ import annotations

from term.ops import FuncCallOp, MethodCallOp
from term.types import FloatType

from every._abc import IntArg, RValue
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .cls import Series
from .type import PointType, SeriesType


__all__ = [
    "SeriesRef",
]


class SeriesRef(CollectionItemRefBase[list, SeriesType], PrimitiveRef):
    """Reference to Series in storage."""

    def set(self, value: Series | list | SeriesType | RValue) -> SeriesType:
        """Set series."""
        if isinstance(value, Series):
            val = value.to_list()
        elif isinstance(value, list):
            val = value
        else:
            val = MethodCallOp(value, "to_list") if isinstance(value, SeriesType) else value
        return SeriesType(TypedSetCmd(self, val))

    def get(self) -> SeriesType:
        """Get series."""
        return SeriesType(FuncCallOp(Series.from_list, GetOp(self)))

    # Convenience methods
    def latest(self) -> PointType:
        """Get most recent point."""
        return self.get().latest()

    def sma(self, period: IntArg) -> FloatType:
        """Simple Moving Average."""
        return self.get().sma(period)

    def ema(self, period: IntArg) -> FloatType:
        """Exponential Moving Average."""
        return self.get().ema(period)

    def rsi(self, period: int = 14) -> FloatType:
        """Relative Strength Index."""
        return self.get().rsi(period)

    def min(self, period: int | None = None) -> FloatType:
        """Minimum value."""
        return self.get().min(period)

    def max(self, period: int | None = None) -> FloatType:
        """Maximum value."""
        return self.get().max(period)

    def avg(self, period: int | None = None) -> FloatType:
        """Average value."""
        return self.get().avg(period)

    def change_pct(self) -> FloatType:
        """Percentage change."""
        return self.get().change_pct()
