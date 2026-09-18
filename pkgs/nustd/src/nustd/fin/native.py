"""Native financial value types - ``PyPercentage`` and ``PyBasisPoint``.

Plain immutable dataclasses, the way ``decimal.Decimal`` or ``fractions.Fraction``
are plain stdlib types. The ``Py`` prefix marks them as the raw Python values (so
they import without aliasing next to the ``Percentage`` / ``BasisPoint`` Forms in
``forms``); the ``interactions`` atoms bind their constructors and methods.

- ``PyPercentage`` stores a float (``75.5`` = 75.5%).
- ``PyBasisPoint`` stores an int (``500`` = 5%), one basis point being 1/100th of
  a percent.
"""

from __future__ import annotations

from dataclasses import dataclass


__all__ = ["PyBasisPoint", "PyPercentage"]


@dataclass(frozen=True, slots=True)
class PyPercentage:
    """A percentage, stored as a float (``75.5`` = 75.5%).

    Examples:
        >>> PyPercentage(75.5)            # 75.5%
        >>> PyPercentage.from_dec(0.755)  # 75.5%
        >>> PyPercentage.from_bps(7550)   # 75.5%
    """

    value: float

    # --- constructors --------------------------------------------------------

    @classmethod
    def from_dec(cls, dec: float) -> PyPercentage:
        """Build from a decimal ratio (``0.755`` -> 75.5%)."""
        return cls(dec * 100)

    @classmethod
    def from_bps(cls, bps: int) -> PyPercentage:
        """Build from basis points (``7550`` -> 75.5%)."""
        return cls(bps / 100)

    @classmethod
    def from_ratio(cls, numerator: float, denominator: float) -> PyPercentage:
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

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> PyPercentage:
        """This percentage clamped to ``[min_val, max_val]``."""
        return PyPercentage(max(min_val, min(max_val, self.value)))

    # --- arithmetic ----------------------------------------------------------

    def __add__(self, other: PyPercentage | float) -> PyPercentage:
        if isinstance(other, PyPercentage):
            return PyPercentage(self.value + other.value)
        return PyPercentage(self.value + other)

    def __radd__(self, other: float) -> PyPercentage:
        return PyPercentage(other + self.value)

    def __sub__(self, other: PyPercentage | float) -> PyPercentage:
        if isinstance(other, PyPercentage):
            return PyPercentage(self.value - other.value)
        return PyPercentage(self.value - other)

    def __rsub__(self, other: float) -> PyPercentage:
        return PyPercentage(other - self.value)

    def __mul__(self, factor: int | float) -> PyPercentage:
        return PyPercentage(self.value * factor)

    def __rmul__(self, factor: int | float) -> PyPercentage:
        return PyPercentage(factor * self.value)

    def __truediv__(self, divisor: int | float) -> PyPercentage:
        return PyPercentage(self.value / divisor)

    def __neg__(self) -> PyPercentage:
        return PyPercentage(-self.value)

    # --- comparison ----------------------------------------------------------

    def __lt__(self, other: PyPercentage | float) -> bool:
        if isinstance(other, PyPercentage):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: PyPercentage | float) -> bool:
        if isinstance(other, PyPercentage):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: PyPercentage | float) -> bool:
        if isinstance(other, PyPercentage):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: PyPercentage | float) -> bool:
        if isinstance(other, PyPercentage):
            return self.value >= other.value
        return self.value >= other

    # --- string --------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.value:.2f}%"

    def format(self, precision: int = 2) -> str:
        """Formatted string, e.g. ``"75.50%"``."""
        return f"{self.value:.{precision}f}%"


@dataclass(frozen=True, slots=True)
class PyBasisPoint:
    """A basis point count - 1/100th of a percent, stored as an int.

    Integer storage keeps rate/fee math exact (no binary-float drift).

    Examples:
        >>> PyBasisPoint(500)            # 5%
        >>> PyBasisPoint.from_pct(5.0)   # 500 bps
        >>> PyBasisPoint.from_dec(0.05)  # 500 bps
    """

    value: int

    # --- constructors --------------------------------------------------------

    @classmethod
    def from_pct(cls, pct: float) -> PyBasisPoint:
        """Build from a percentage (``5.0`` -> 500 bps)."""
        return cls(int(pct * 100))

    @classmethod
    def from_dec(cls, dec: float) -> PyBasisPoint:
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

    def __add__(self, other: PyBasisPoint | int) -> PyBasisPoint:
        if isinstance(other, PyBasisPoint):
            return PyBasisPoint(self.value + other.value)
        return PyBasisPoint(self.value + other)

    def __radd__(self, other: int) -> PyBasisPoint:
        return PyBasisPoint(other + self.value)

    def __sub__(self, other: PyBasisPoint | int) -> PyBasisPoint:
        if isinstance(other, PyBasisPoint):
            return PyBasisPoint(self.value - other.value)
        return PyBasisPoint(self.value - other)

    def __rsub__(self, other: int) -> PyBasisPoint:
        return PyBasisPoint(other - self.value)

    def __mul__(self, factor: int | float) -> PyBasisPoint:
        return PyBasisPoint(int(self.value * factor))

    def __rmul__(self, factor: int | float) -> PyBasisPoint:
        return PyBasisPoint(int(factor * self.value))

    def __truediv__(self, divisor: int | float) -> PyBasisPoint:
        return PyBasisPoint(int(self.value / divisor))

    def __floordiv__(self, divisor: int) -> PyBasisPoint:
        return PyBasisPoint(self.value // divisor)

    # --- comparison ----------------------------------------------------------

    def __lt__(self, other: PyBasisPoint | int) -> bool:
        if isinstance(other, PyBasisPoint):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: PyBasisPoint | int) -> bool:
        if isinstance(other, PyBasisPoint):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: PyBasisPoint | int) -> bool:
        if isinstance(other, PyBasisPoint):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: PyBasisPoint | int) -> bool:
        if isinstance(other, PyBasisPoint):
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
