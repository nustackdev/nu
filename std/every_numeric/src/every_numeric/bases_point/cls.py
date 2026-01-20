"""Basis Point python native type."""

from __future__ import annotations

from dataclasses import dataclass


__all__ = [
    "BasisPoint",
]


# =============================================================================
# NATIVE PYTHON TYPE
# =============================================================================


@dataclass(frozen=True, slots=True)
class BasisPoint:
    """Basis points - 1/100th of a percent.

    Immutable value type for precise rate/fee representation.
    Stored as int to avoid floating point issues.

    Examples:
        >>> BasisPoint(500)           # 5%
        >>> BasisPoint.from_pct(5.0)  # 500 bps
        >>> BasisPoint.from_dec(0.05) # 500 bps
    """

    value: int

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_pct(cls, pct: float) -> BasisPoint:
        """Create from percentage.

        Args:
            pct: Percentage (5.0 = 5%).

        Returns:
            BasisPoint equivalent.
        """
        return cls(int(pct * 100))

    @classmethod
    def from_dec(cls, dec: float) -> BasisPoint:
        """Create from decimal.

        Args:
            dec: Decimal (0.05 = 5%).

        Returns:
            BasisPoint equivalent.
        """
        return cls(int(dec * 10000))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> float:
        """Convert to percentage.

        Returns:
            Percentage (500 bps -> 5.0).
        """
        return self.value / 100

    def to_dec(self) -> float:
        """Convert to decimal.

        Returns:
            Decimal (500 bps -> 0.05).
        """
        return self.value / 10000

    def to_int(self) -> int:
        """Get raw basis points.

        Returns:
            Raw int value.
        """
        return self.value

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float) -> float:
        """Apply basis points to an amount.

        Args:
            amount: Value to apply rate to.

        Returns:
            amount * bps / 10000
        """
        return amount * self.value / 10000

    def add_to(self, amount: int | float) -> float:
        """Add basis points to an amount.

        Args:
            amount: Base value.

        Returns:
            amount * (1 + bps/10000)
        """
        return amount * (1 + self.value / 10000)

    def sub_from(self, amount: int | float) -> float:
        """Subtract basis points from an amount.

        Args:
            amount: Base value.

        Returns:
            amount * (1 - bps/10000)
        """
        return amount * (1 - self.value / 10000)

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: BasisPoint | int) -> BasisPoint:
        """Add basis points."""
        if isinstance(other, BasisPoint):
            return BasisPoint(self.value + other.value)
        return BasisPoint(self.value + other)

    def __radd__(self, other: int) -> BasisPoint:
        """Right add."""
        return BasisPoint(other + self.value)

    def __sub__(self, other: BasisPoint | int) -> BasisPoint:
        """Subtract basis points."""
        if isinstance(other, BasisPoint):
            return BasisPoint(self.value - other.value)
        return BasisPoint(self.value - other)

    def __rsub__(self, other: int) -> BasisPoint:
        """Right subtract."""
        return BasisPoint(other - self.value)

    def __mul__(self, factor: int | float) -> BasisPoint:
        """Multiply by factor."""
        return BasisPoint(int(self.value * factor))

    def __rmul__(self, factor: int | float) -> BasisPoint:
        """Right multiply."""
        return BasisPoint(int(factor * self.value))

    def __truediv__(self, divisor: int | float) -> BasisPoint:
        """Divide by factor."""
        return BasisPoint(int(self.value / divisor))

    def __floordiv__(self, divisor: int) -> BasisPoint:
        """Floor divide."""
        return BasisPoint(self.value // divisor)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __lt__(self, other: BasisPoint | int) -> bool:
        """Less than."""
        if isinstance(other, BasisPoint):
            return self.value < other.value
        return self.value < other

    def __le__(self, other: BasisPoint | int) -> bool:
        """Less than or equal."""
        if isinstance(other, BasisPoint):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other: BasisPoint | int) -> bool:
        """Greater than."""
        if isinstance(other, BasisPoint):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other: BasisPoint | int) -> bool:
        """Greater than or equal."""
        if isinstance(other, BasisPoint):
            return self.value >= other.value
        return self.value >= other

    # =========================================================================
    # STRING
    # =========================================================================

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value}bps"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"BasisPoint({self.value})"

    def format(self, style: str = "bps") -> str:
        """Format as string.

        Args:
            style: 'bps' (500bps), 'pct' (5.00%), 'dec' (0.0500)

        Returns:
            Formatted string.
        """
        if style == "pct":
            return f"{self.to_pct():.2f}%"
        elif style == "dec":
            return f"{self.to_dec():.4f}"
        return f"{self.value}bps"
