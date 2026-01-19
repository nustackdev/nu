"""Series native Python types."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field


__all__ = [
    "Point",
    "Series",
]


# =============================================================================
# NATIVE PYTHON TYPES
# =============================================================================


@dataclass(frozen=True, slots=True)
class Point:
    """Single data point in a time series.

    Core fields:
    - value: The primary numeric value
    - timestamp: Unix timestamp (optional)

    Can be extended with extra data via `data` dict.

    Examples:
        >>> Point(100.0)
        >>> Point(100.0, timestamp=1234567890)
        >>> Point(100.0, timestamp=1234567890, data={"volume": 1000})
    """

    value: float
    timestamp: int = 0
    data: dict = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        """Get extra data field.

        Args:
            key: Field name.
            default: Default if not found.

        Returns:
            Field value.
        """
        return self.data.get(key, default)

    def with_data(self, **kwargs: float) -> Point:
        """Create new Point with additional data.

        Args:
            **kwargs: Extra data fields.

        Returns:
            New Point with merged data.
        """
        return Point(
            value=self.value,
            timestamp=self.timestamp,
            data={**self.data, **kwargs},
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            **self.data,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Point:
        """Create from dictionary."""
        value = d.get("value", 0.0)
        timestamp = d.get("timestamp", 0)
        data = {k: v for k, v in d.items() if k not in ("value", "timestamp")}
        return cls(value=value, timestamp=timestamp, data=data)

    def __str__(self) -> str:
        return f"Point({self.value}, t={self.timestamp})"


@dataclass
class Series:
    """Time series of data points.

    Provides calculations over the series:
    - Moving averages (SMA, EMA)
    - Min/Max/Avg over windows
    - Rate of change
    - Custom aggregations

    Examples:
        >>> s = Series()
        >>> s.append(Point(100.0))
        >>> s.append(Point(110.0))
        >>> s.sma(2)  # 105.0
    """

    points: list[Point] = field(default_factory=list)

    # =========================================================================
    # ACCESS
    # =========================================================================

    def __len__(self) -> int:
        """Number of points."""
        return len(self.points)

    def __iter__(self) -> Iterator[Point]:
        """Iterate over points."""
        return iter(self.points)

    def __getitem__(self, index: int) -> Point:
        """Get point by index."""
        return self.points[index]

    def latest(self) -> Point:
        """Get most recent point."""
        if not self.points:
            return Point(0.0)
        return self.points[-1]

    def first(self) -> Point:
        """Get first point."""
        if not self.points:
            return Point(0.0)
        return self.points[0]

    def at(self, index: int) -> Point:
        """Get point at index (supports negative)."""
        if not self.points or index >= len(self.points) or index < -len(self.points):
            return Point(0.0)
        return self.points[index]

    def values(self, n: int | None = None) -> list[float]:
        """Get values, optionally last n.

        Args:
            n: Number of latest values (None = all).

        Returns:
            List of values.
        """
        if n is None:
            return [p.value for p in self.points]
        return [p.value for p in self.points[-n:]]

    # =========================================================================
    # MUTATION
    # =========================================================================

    def append(self, point: Point | float) -> Series:
        """Append point, return new Series.

        Args:
            point: Point or value to append.

        Returns:
            New Series with appended point.
        """
        if isinstance(point, (int, float)):
            point = Point(float(point))
        return Series(points=self.points + [point])

    def slice(self, start: int, end: int | None = None) -> Series:
        """Get slice of series.

        Args:
            start: Start index.
            end: End index (exclusive).

        Returns:
            New Series slice.
        """
        if end is None:
            return Series(points=self.points[start:])
        return Series(points=self.points[start:end])

    def tail(self, n: int) -> Series:
        """Get last n points.

        Args:
            n: Number of points.

        Returns:
            New Series with last n points.
        """
        return Series(points=self.points[-n:])

    # =========================================================================
    # CALCULATIONS - MOVING AVERAGES
    # =========================================================================

    def sma(self, period: int) -> float:
        """Simple Moving Average.

        Args:
            period: Number of periods.

        Returns:
            SMA of last `period` values.
        """
        if not self.points:
            return 0.0
        n = min(period, len(self.points))
        if n == 0:
            return 0.0
        return sum(p.value for p in self.points[-n:]) / n

    def ema(self, period: int) -> float:
        """Exponential Moving Average.

        Uses smoothing factor k = 2 / (period + 1).

        Args:
            period: Number of periods.

        Returns:
            EMA.
        """
        if not self.points:
            return 0.0
        n = min(period, len(self.points))
        if n == 0:
            return 0.0

        k = 2 / (period + 1)
        ema = sum(p.value for p in self.points[:n]) / n

        for p in self.points[n:]:
            ema = p.value * k + ema * (1 - k)

        return ema

    def wma(self, period: int) -> float:
        """Weighted Moving Average.

        Recent values weighted more heavily.

        Args:
            period: Number of periods.

        Returns:
            WMA.
        """
        if not self.points:
            return 0.0
        n = min(period, len(self.points))
        if n == 0:
            return 0.0

        values = [p.value for p in self.points[-n:]]
        weights = list(range(1, n + 1))
        return sum(v * w for v, w in zip(values, weights, strict=False)) / sum(weights)

    # =========================================================================
    # CALCULATIONS - STATISTICS
    # =========================================================================

    def min(self, period: int | None = None) -> float:
        """Minimum value.

        Args:
            period: Look-back period (None = all).

        Returns:
            Minimum value.
        """
        if not self.points:
            return 0.0
        subset = self.points[-period:] if period else self.points
        return min(p.value for p in subset) if subset else 0.0

    def max(self, period: int | None = None) -> float:
        """Maximum value.

        Args:
            period: Look-back period (None = all).

        Returns:
            Maximum value.
        """
        if not self.points:
            return 0.0
        subset = self.points[-period:] if period else self.points
        return max(p.value for p in subset) if subset else 0.0

    def avg(self, period: int | None = None) -> float:
        """Average value.

        Args:
            period: Look-back period (None = all).

        Returns:
            Average value.
        """
        if not self.points:
            return 0.0
        subset = self.points[-period:] if period else self.points
        if not subset:
            return 0.0
        return sum(p.value for p in subset) / len(subset)

    def sum(self, period: int | None = None) -> float:
        """Sum of values.

        Args:
            period: Look-back period (None = all).

        Returns:
            Sum of values.
        """
        if not self.points:
            return 0.0
        subset = self.points[-period:] if period else self.points
        return sum(p.value for p in subset)

    def std(self, period: int | None = None) -> float:
        """Standard deviation.

        Args:
            period: Look-back period (None = all).

        Returns:
            Standard deviation.
        """
        if not self.points:
            return 0.0
        subset = self.points[-period:] if period else self.points
        if len(subset) < 2:
            return 0.0
        avg = sum(p.value for p in subset) / len(subset)
        variance = sum((p.value - avg) ** 2 for p in subset) / len(subset)
        return variance**0.5

    # =========================================================================
    # CALCULATIONS - RATE OF CHANGE
    # =========================================================================

    def change(self) -> float:
        """Absolute change from first to last.

        Returns:
            last - first
        """
        if len(self.points) < 2:
            return 0.0
        return self.points[-1].value - self.points[0].value

    def change_pct(self) -> float:
        """Percentage change from first to last.

        Returns:
            (last - first) / first * 100
        """
        if len(self.points) < 2:
            return 0.0
        first = self.points[0].value
        if first == 0:
            return 0.0
        return (self.points[-1].value - first) / first * 100

    def roc(self, period: int = 1) -> float:
        """Rate of change over period.

        Args:
            period: Look-back period.

        Returns:
            (current - n_periods_ago) / n_periods_ago * 100
        """
        if len(self.points) <= period:
            return 0.0
        old = self.points[-period - 1].value
        if old == 0:
            return 0.0
        return (self.points[-1].value - old) / old * 100

    # =========================================================================
    # CALCULATIONS - INDICATORS
    # =========================================================================

    def rsi(self, period: int = 14) -> float:
        """Relative Strength Index.

        RSI = 100 - (100 / (1 + RS))
        RS = avg_gain / avg_loss

        Args:
            period: RSI period.

        Returns:
            RSI (0-100).
        """
        if len(self.points) < period + 1:
            return 50.0

        gains = []
        losses = []

        for i in range(-period, 0):
            change = self.points[i].value - self.points[i - 1].value
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def bollinger(self, period: int = 20, std_dev: float = 2.0) -> tuple[float, float, float]:
        """Bollinger Bands.

        Args:
            period: SMA period.
            std_dev: Standard deviation multiplier.

        Returns:
            (lower, middle, upper) bands.
        """
        middle = self.sma(period)
        std = self.std(period)
        return (middle - std_dev * std, middle, middle + std_dev * std)

    # =========================================================================
    # AGGREGATION
    # =========================================================================

    def aggregate(
        self,
        func: Callable[[list[float]], float],
        period: int | None = None,
    ) -> float:
        """Apply custom aggregation function.

        Args:
            func: Function taking list of values.
            period: Look-back period (None = all).

        Returns:
            Aggregation result.
        """
        values = self.values(period)
        if not values:
            return 0.0
        return func(values)

    def map(self, func: Callable[[float], float]) -> Series:
        """Map function over values.

        Args:
            func: Function to apply to each value.

        Returns:
            New Series with mapped values.
        """
        return Series(points=[Point(func(p.value), p.timestamp, p.data) for p in self.points])

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_list(self) -> list[dict]:
        """Convert to list of dicts."""
        return [p.to_dict() for p in self.points]

    @classmethod
    def from_list(cls, data: list[dict]) -> Series:
        """Create from list of dicts."""
        return cls(points=[Point.from_dict(d) for d in data])

    def __str__(self) -> str:
        return f"Series({len(self.points)} points)"
