"""Time series type for Shape system.

Generic time-series data with built-in calculations:
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- Min/Max/Avg over windows
- Rate of change

This module provides both native Python classes and Shape-compatible types.

Example:
    from everybase.type import SeriesSlot

    class PriceHistory(Shape):
        prices = SeriesSlot()

    # Append data
    PriceHistory.prices.append(Point(100.0, timestamp=1234567890))

    # Calculations
    PriceHistory.prices.sma(20)     # 20-period SMA
    PriceHistory.prices.ema(12)     # 12-period EMA
    PriceHistory.prices.max(50)     # 50-period high
"""

from __future__ import annotations

from .args import PointArg, SeriesArg
from .cls import Point, Series
from .ref import SeriesRef
from .slot import SeriesSlot
from .type import PointType, SeriesType


__all__ = [
    # Native Python classes
    "Point",
    "Series",
    # Shape types
    "PointType",
    "SeriesType",
    "SeriesRef",
    "SeriesSlot",
    # Args
    "SeriesArg",
    "PointArg",
]
