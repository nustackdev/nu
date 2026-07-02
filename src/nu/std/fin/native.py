"""Native financial value types - ``Percentage`` and ``BasisPoint``.

Plain immutable dataclasses, the way ``decimal.Decimal`` or ``fractions.Fraction``
are plain stdlib types. The Nu Forms in ``forms`` wrap these; the ``interactions``
atoms bind their constructors and methods.

- ``Percentage`` stores a float (``75.5`` = 75.5%).
- ``BasisPoint`` stores an int (``500`` = 5%), one basis point being 1/100th of
  a percent.
"""

from __future__ import annotations

from dataclasses import dataclass


__all__ = ["BasisPoint", "Percentage"]


@dataclass(frozen=True, slots=True)
class Percentage:
    """A percentage, stored as a float (``75.5`` = 75.5%).

    Examples:
        >>> Percentage(75.5)            # 75.5%
        >>> Percentage.from_dec(0.755)  # 75.5%
        >>> Percentage.from_bps(7550)   # 75.5%
    """

    value: float

    # --- constructors --------------------------------------------------------

    @classmethod
    def from_dec(cls, dec: float) -> Percentage:
        """Build from a decimal ratio (``0.755`` -> 75.5%)."""
        return cls(dec * 100)

    @classmethod
    def from_bps(cls, bps: int) -> Percentage:
        """Build from basis points (``7550`` -> 75.5%)."""
        return cls(bps / 100)

    @classmethod
    def from_ratio(cls, numerator: float, denominator: float) -> Percentage:
        """Build from a ratio (``3 / 4`` -> 75%). Zero denominator -> 0%."""
        if denominator == 0:
            return cls(0.0)
        return cls((numerator / denominator) * 100)

    # --- conversions ---------------------------------------------------------

    def to_dec(self) -> float:
        """The decimal ratio (75.5% -> ``0.755``)."""
        return self.value / 100

    def to_bps(self) -> int:
        """The basis points (75.5% -> ``7550``)."""
        return int(self.value * 100)

    def to_float(self) -> float:
        """The raw percentage value."""
        return self.value

    def __float__(self) -> float:
        return self.value

    # --- application ---------------------------------------------------------

    def apply(self, amount: int | float) -> float:
        """This percentage of ``amount``."""
        return amount * self.value / 100

    def add_to(self, amount: int | float) -> float:
        """``amount`` grown by this percentage."""
        return amount * (1 + self.value / 100)

    def sub_from(self, amount: int | float) -> float:
        """``amount`` reduced by this percentage."""
        return amount * (1 - self.value / 100)

    # --- validation ----------------------------------------------------------

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> bool:
        """Whether the value falls within ``[min_val, max_val]``."""
        return min_val <= self.value <= max_val

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> Percentage:
        """This percentage clamped to ``[min_val, max_val]``."""
        return Percentage(max(min_val, min(max_val, self.value)))

    # --- arithmetic ----------------------------------------------------------

    def __add__(self, other: Percentage | float) -> Percentage:
        if isinstance(other, Percentage):
            return Percentage(self.value + other.value)
        return Percentage(self.value + other)

    def __radd__(self, other: float) -> Percentage:
        return Percentage(other + self.value)

    def __sub__(self, other: Percentage | float) -> Percentage:
        if isinstance(other, Percentage):
            return Percentage(self.value - other.value)
        return Percentage(self.value - other)

    def __rsub__(self, other: float) -> Percentage:
        return Percentage(other - self.value)

    def __mul__(self, factor: int | float) -> Percentage:
        return Percentage(self.value * factor)

    def __rmul__(self, factor: int | float) -> Percentage:
        return Percentage(factor * self.value)

    def __truediv__(self, divisor: int | float) -> Percentage:
        return Percentage(self.value / divisor)

    def __neg__(self) -> Percentage:
        return Percentage(-self.value)

    # --- comparison ----------------------------------------------------------

    def __lt__(self, other: Percentage | float) -> bool:
        if isinstance(other, Percentage):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: Percentage | float) -> bool:
        if isinstance(other, Percentage):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: Percentage | float) -> bool:
        if isinstance(other, Percentage):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: Percentage | float) -> bool:
        if isinstance(other, Percentage):
            return self.value >= other.value
        return self.value >= other

    # --- string --------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.value:.2f}%"

    def format(self, precision: int = 2) -> str:
        """Formatted string, e.g. ``"75.50%"``."""
        return f"{self.value:.{precision}f}%"


@dataclass(frozen=True, slots=True)
class BasisPoint:
    """A basis point count - 1/100th of a percent, stored as an int.

    Integer storage keeps rate/fee math exact (no binary-float drift).

    Examples:
        >>> BasisPoint(500)            # 5%
        >>> BasisPoint.from_pct(5.0)   # 500 bps
        >>> BasisPoint.from_dec(0.05)  # 500 bps
    """

    value: int

    # --- constructors --------------------------------------------------------

    @classmethod
    def from_pct(cls, pct: float) -> BasisPoint:
        """Build from a percentage (``5.0`` -> 500 bps)."""
        return cls(int(pct * 100))

    @classmethod
    def from_dec(cls, dec: float) -> BasisPoint:
        """Build from a decimal ratio (``0.05`` -> 500 bps)."""
        return cls(int(dec * 10000))

    # --- conversions ---------------------------------------------------------

    def to_pct(self) -> float:
        """The percentage (500 bps -> ``5.0``)."""
        return self.value / 100

    def to_dec(self) -> float:
        """The decimal ratio (500 bps -> ``0.05``)."""
        return self.value / 10000

    def to_int(self) -> int:
        """The raw basis-point count."""
        return self.value

    def __int__(self) -> int:
        return self.value

    # --- application ---------------------------------------------------------

    def apply(self, amount: int | float) -> float:
        """This many basis points of ``amount``."""
        return amount * self.value / 10000

    def add_to(self, amount: int | float) -> float:
        """``amount`` grown by these basis points."""
        return amount * (1 + self.value / 10000)

    def sub_from(self, amount: int | float) -> float:
        """``amount`` reduced by these basis points."""
        return amount * (1 - self.value / 10000)

    # --- arithmetic ----------------------------------------------------------

    def __add__(self, other: BasisPoint | int) -> BasisPoint:
        if isinstance(other, BasisPoint):
            return BasisPoint(self.value + other.value)
        return BasisPoint(self.value + other)

    def __radd__(self, other: int) -> BasisPoint:
        return BasisPoint(other + self.value)

    def __sub__(self, other: BasisPoint | int) -> BasisPoint:
        if isinstance(other, BasisPoint):
            return BasisPoint(self.value - other.value)
        return BasisPoint(self.value - other)

    def __rsub__(self, other: int) -> BasisPoint:
        return BasisPoint(other - self.value)

    def __mul__(self, factor: int | float) -> BasisPoint:
        return BasisPoint(int(self.value * factor))

    def __rmul__(self, factor: int | float) -> BasisPoint:
        return BasisPoint(int(factor * self.value))

    def __truediv__(self, divisor: int | float) -> BasisPoint:
        return BasisPoint(int(self.value / divisor))

    def __floordiv__(self, divisor: int) -> BasisPoint:
        return BasisPoint(self.value // divisor)

    # --- comparison ----------------------------------------------------------

    def __lt__(self, other: BasisPoint | int) -> bool:
        if isinstance(other, BasisPoint):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: BasisPoint | int) -> bool:
        if isinstance(other, BasisPoint):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: BasisPoint | int) -> bool:
        if isinstance(other, BasisPoint):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: BasisPoint | int) -> bool:
        if isinstance(other, BasisPoint):
            return self.value >= other.value
        return self.value >= other

    # --- string --------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.value}bps"

    def format(self, style: str = "bps") -> str:
        """Formatted string in ``"bps"``, ``"pct"``, or ``"dec"`` style."""
        if style == "pct":
            return f"{self.to_pct():.2f}%"
        if style == "dec":
            return f"{self.to_dec():.4f}"
        return f"{self.value}bps"
