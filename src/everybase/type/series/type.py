"""Series Type."""

from __future__ import annotations

from everyterm.ops import FuncCallOp, LenOp, MethodCallOp
from everyterm.term import FloatArg, IntArg
from everyterm.types import BaseType, FloatType, IntType
from everyterm.typing import Sentinel

from .args import PointArg
from .cls import Point, Series


__all__ = [
    "PointType",
    "SeriesType",
]


class PointType(
    BaseType[Point | dict | Sentinel],
):
    """Type wrapping Point."""

    @classmethod
    def create(
        cls,
        value: FloatArg,
        timestamp: IntArg = 0,
        **data: FloatArg,
    ) -> PointType:
        """Create Point."""
        return cls(FuncCallOp(lambda v, t, **d: Point(v, t, d), value, timestamp, **data))

    def value(self) -> FloatType:
        """Get primary value."""
        return FloatType(FuncCallOp(getattr, self, "value"))

    def timestamp(self) -> IntType:
        """Get timestamp."""
        return IntType(FuncCallOp(getattr, self, "timestamp"))

    def get(self, key: str, default: float = 0.0) -> FloatType:
        """Get extra data field."""
        return FloatType(MethodCallOp(self, "get", key, default))


class SeriesType(
    BaseType[Series | list | Sentinel],
):
    """Type wrapping Series."""

    @classmethod
    def empty(cls) -> SeriesType:
        """Create empty series."""
        return cls(FuncCallOp(Series))

    # =========================================================================
    # ACCESS
    # =========================================================================

    def length(self) -> IntType:
        """Number of points."""
        return IntType(LenOp(self))

    def latest(self) -> PointType:
        """Get most recent point."""
        return PointType(MethodCallOp(self, "latest"))

    def first(self) -> PointType:
        """Get first point."""
        return PointType(MethodCallOp(self, "first"))

    def at(self, index: IntArg) -> PointType:
        """Get point at index."""
        return PointType(MethodCallOp(self, "at", index))

    # =========================================================================
    # MOVING AVERAGES
    # =========================================================================

    def sma(self, period: IntArg) -> FloatType:
        """Simple Moving Average."""
        return FloatType(MethodCallOp(self, "sma", period))

    def ema(self, period: IntArg) -> FloatType:
        """Exponential Moving Average."""
        return FloatType(MethodCallOp(self, "ema", period))

    def wma(self, period: IntArg) -> FloatType:
        """Weighted Moving Average."""
        return FloatType(MethodCallOp(self, "wma", period))

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def min(self, period: int | None = None) -> FloatType:
        """Minimum value."""
        return FloatType(MethodCallOp(self, "min", period))

    def max(self, period: int | None = None) -> FloatType:
        """Maximum value."""
        return FloatType(MethodCallOp(self, "max", period))

    def avg(self, period: int | None = None) -> FloatType:
        """Average value."""
        return FloatType(MethodCallOp(self, "avg", period))

    def sum(self, period: int | None = None) -> FloatType:
        """Sum of values."""
        return FloatType(MethodCallOp(self, "sum", period))

    def std(self, period: int | None = None) -> FloatType:
        """Standard deviation."""
        return FloatType(MethodCallOp(self, "std", period))

    # =========================================================================
    # RATE OF CHANGE
    # =========================================================================

    def change(self) -> FloatType:
        """Absolute change."""
        return FloatType(MethodCallOp(self, "change"))

    def change_pct(self) -> FloatType:
        """Percentage change."""
        return FloatType(MethodCallOp(self, "change_pct"))

    def roc(self, period: int = 1) -> FloatType:
        """Rate of change."""
        return FloatType(MethodCallOp(self, "roc", period))

    # =========================================================================
    # INDICATORS
    # =========================================================================

    def rsi(self, period: int = 14) -> FloatType:
        """Relative Strength Index."""
        return FloatType(MethodCallOp(self, "rsi", period))

    # =========================================================================
    # MUTATION
    # =========================================================================

    def append(self, point: PointArg | FloatArg) -> SeriesType:
        """Append point."""
        if isinstance(point, Point):
            point = PointType(point)
        return SeriesType(MethodCallOp(self, "append", point))

    def tail(self, n: IntArg) -> SeriesType:
        """Get last n points."""
        return SeriesType(MethodCallOp(self, "tail", n))
