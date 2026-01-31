"""Percentage native Python type."""

from __future__ import annotations

from dataclasses import dataclass


__all__ = [
    "Percentage",
]


@dataclass(frozen=True, slots=True)
class Percentage:
    """Percentage value.

    Stored as float (75.5 = 75.5%).
    Immutable value type.

    Examples:
        >>> Percentage(75.5)           # 75.5%
        >>> Percentage.from_dec(0.755) # 75.5%
        >>> Percentage.from_bps(7550)  # 75.5%
    """

    value: float

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_dec(cls, dec: float) -> Percentage:
        """Create from decimal."""
        return cls(dec * 100)

    @classmethod
    def from_bps(cls, bps: int) -> Percentage:
        """Create from basis points."""
        return cls(bps / 100)

    @classmethod
    def from_ratio(cls, numerator: float, denominator: float) -> Percentage:
        """Create from ratio."""
        if denominator == 0:
            return cls(0.0)
        return cls((numerator / denominator) * 100)

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_dec(self) -> float:
        """Convert to decimal."""
        return self.value / 100

    def to_bps(self) -> int:
        """Convert to basis points."""
        return int(self.value * 100)

    def to_float(self) -> float:
        """Get raw percentage."""
        return self.value

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float) -> float:
        """Apply percentage to amount."""
        return amount * self.value / 100

    def of(self, amount: int | float) -> float:
        """Alias for apply."""
        return self.apply(amount)

    def add_to(self, amount: int | float) -> float:
        """Add percentage to amount."""
        return amount * (1 + self.value / 100)

    def sub_from(self, amount: int | float) -> float:
        """Subtract percentage from amount."""
        return amount * (1 - self.value / 100)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> bool:
        """Check if percentage is within range."""
        return min_val <= self.value <= max_val

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> Percentage:
        """Clamp to range."""
        return Percentage(max(min_val, min(max_val, self.value)))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: Percentage | float) -> Percentage:
        """Add percentages."""
        if isinstance(other, Percentage):
            return Percentage(self.value + other.value)
        return Percentage(self.value + other)

    def __radd__(self, other: float) -> Percentage:
        """Right add."""
        return Percentage(other + self.value)

    def __sub__(self, other: Percentage | float) -> Percentage:
        """Subtract percentages."""
        if isinstance(other, Percentage):
            return Percentage(self.value - other.value)
        return Percentage(self.value - other)

    def __rsub__(self, other: float) -> Percentage:
        """Right subtract."""
        return Percentage(other - self.value)

    def __mul__(self, factor: int | float) -> Percentage:
        """Multiply by factor."""
        return Percentage(self.value * factor)

    def __rmul__(self, factor: int | float) -> Percentage:
        """Right multiply."""
        return Percentage(factor * self.value)

    def __truediv__(self, divisor: int | float) -> Percentage:
        """Divide by factor."""
        return Percentage(self.value / divisor)

    def __neg__(self) -> Percentage:
        """Negate."""
        return Percentage(-self.value)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __lt__(self, other: Percentage | float) -> bool:
        """Less than."""
        if isinstance(other, Percentage):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: Percentage | float) -> bool:
        """Less than or equal."""
        if isinstance(other, Percentage):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: Percentage | float) -> bool:
        """Greater than."""
        if isinstance(other, Percentage):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: Percentage | float) -> bool:
        """Greater than or equal."""
        if isinstance(other, Percentage):
            return self.value >= other.value
        return self.value >= other

    # =========================================================================
    # STRING
    # =========================================================================

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.2f}%"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Percentage({self.value})"

    def format(self, precision: int = 2) -> str:
        """Format as string."""
        return f"{self.value:.{precision}f}%"
