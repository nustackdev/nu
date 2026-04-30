"""Financial types - Percentage and BasisPoint.

Native Python types (dataclasses) + Nu interfaces.
Percentage stores as float (75.5 = 75.5%).
BasisPoint stores as int (500 = 5%), 1/100th of a percent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu import Arg
    from nu.primitives import BoolI, FloatI, IntI
    from nu.terms import Nu


__all__ = [
    "BasisPoint",
    "BasisPointArg",
    "BasisPointI",
    "Percentage",
    "PercentageArg",
    "PercentageI",
]


# =============================================================================
# TYPE ALIASES
# =============================================================================

type PercentageArg = Arg[Percentage]
type BasisPointArg = Arg[BasisPoint]


# =============================================================================
# NATIVE TYPES
# =============================================================================


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

    def __float__(self) -> float:
        """Convert to float (raw percentage value)."""
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
        """Create from percentage."""
        return cls(int(pct * 100))

    @classmethod
    def from_dec(cls, dec: float) -> BasisPoint:
        """Create from decimal."""
        return cls(int(dec * 10000))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> float:
        """Convert to percentage."""
        return self.value / 100

    def to_dec(self) -> float:
        """Convert to decimal."""
        return self.value / 10000

    def to_int(self) -> int:
        """Get raw basis points."""
        return self.value

    def __int__(self) -> int:
        """Convert to int (raw basis points)."""
        return self.value

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float) -> float:
        """Apply basis points to an amount."""
        return amount * self.value / 10000

    def add_to(self, amount: int | float) -> float:
        """Add basis points to an amount."""
        return amount * (1 + self.value / 10000)

    def sub_from(self, amount: int | float) -> float:
        """Subtract basis points from an amount."""
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
        """Format as string."""
        if style == "pct":
            return f"{self.to_pct():.2f}%"
        elif style == "dec":
            return f"{self.to_dec():.4f}"
        return f"{self.value}bps"


# =============================================================================
# PERCENTAGE INTERFACE
# =============================================================================


class _PercentageI(Interface):
    """Mixin for Percentage operations."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> PercentageI:
        """Create from percentage float."""
        from nu.terms import FuncCall

        return PercentageI(FuncCall(Percentage, value))

    @classmethod
    def from_dec(cls, dec: float | Nu[float]) -> PercentageI:
        """Create from decimal."""
        from nu.terms import FuncCall

        return PercentageI(FuncCall(Percentage.from_dec, dec))

    @classmethod
    def from_bps(cls, bps: int | Nu[int]) -> PercentageI:
        """Create from basis points."""
        from nu.terms import FuncCall

        return PercentageI(FuncCall(Percentage.from_bps, bps))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_dec(self) -> FloatI:
        """Convert to decimal."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "to_dec"))

    def to_bps(self) -> IntI:
        """Convert to basis points."""
        from nu.terms import MethodCall
        from nu.primitives import IntI

        return IntI(MethodCall(self, "to_bps"))

    def to_float(self) -> FloatI:
        """Get raw percentage."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "to_float"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Nu) -> FloatI:
        """Apply percentage to amount."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "apply", amount))

    def of(self, amount: int | float | Nu) -> FloatI:
        """Alias for apply."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "of", amount))

    def add_to(self, amount: int | float | Nu) -> FloatI:
        """Add percentage to amount."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "add_to", amount))

    def sub_from(self, amount: int | float | Nu) -> FloatI:
        """Subtract percentage from amount."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "sub_from", amount))

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> BoolI:
        """Check if within range."""
        from nu.terms import MethodCall
        from nu.primitives import BoolI

        return BoolI(MethodCall(self, "is_valid", min_val, max_val))

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> PercentageI:
        """Clamp to range."""
        from nu.terms import MethodCall

        return PercentageI(MethodCall(self, "clamp", min_val, max_val))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: PercentageArg | float) -> PercentageI:
        """Add percentages."""
        from nu import Add

        if isinstance(other, Percentage):
            other = PercentageI(other)
        return PercentageI(Add(self, other))

    def __radd__(self, other: Percentage | float) -> PercentageI:
        """Right add."""
        from nu import Add

        if isinstance(other, Percentage):
            other = PercentageI(other)
        return PercentageI(Add(other, self))

    def __sub__(self, other: PercentageArg | float) -> PercentageI:
        """Subtract percentages."""
        from nu import Sub

        if isinstance(other, Percentage):
            other = PercentageI(other)
        return PercentageI(Sub(self, other))

    def __rsub__(self, other: Percentage | float) -> PercentageI:
        """Right subtract."""
        from nu import Sub

        if isinstance(other, Percentage):
            other = PercentageI(other)
        return PercentageI(Sub(other, self))

    def __mul__(self, factor: int | float | Nu) -> PercentageI:
        """Multiply by factor."""
        from nu import Mul

        return PercentageI(Mul(self, factor))

    def __rmul__(self, factor: int | float) -> PercentageI:
        """Right multiply."""
        from nu import Mul

        return PercentageI(Mul(factor, self))

    def __truediv__(self, divisor: int | float | Nu) -> PercentageI:
        """Divide by factor."""
        from nu import Div

        return PercentageI(Div(self, divisor))

    def __neg__(self) -> PercentageI:
        """Negate."""
        from nu import Neg

        return PercentageI(Neg(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: PercentageArg) -> BoolI:
        """Greater than."""
        from nu import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: PercentageArg) -> BoolI:
        """Less than."""
        from nu import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: PercentageArg) -> BoolI:
        """Greater than or equal."""
        from nu import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: PercentageArg) -> BoolI:
        """Less than or equal."""
        from nu import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: PercentageArg) -> BoolI:
        """Equal."""
        from nu import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: PercentageArg) -> BoolI:
        """Not equal."""
        from nu import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))


class PercentageI(_PercentageI, TypedNu[Percentage]):
    """Computed Percentage value."""

    pass


# =============================================================================
# BASIS POINT INTERFACE
# =============================================================================


class _BasisPointI(Interface):
    """Mixin for BasisPoint operations."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> BasisPointI:
        """Create from raw basis points."""
        from nu.terms import FuncCall

        return BasisPointI(FuncCall(BasisPoint, value))

    @classmethod
    def from_pct(cls, pct: float | Nu[float]) -> BasisPointI:
        """Create from percentage."""
        from nu.terms import FuncCall

        return BasisPointI(FuncCall(BasisPoint.from_pct, pct))

    @classmethod
    def from_dec(cls, dec: float | Nu[float]) -> BasisPointI:
        """Create from decimal."""
        from nu.terms import FuncCall

        return BasisPointI(FuncCall(BasisPoint.from_dec, dec))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> FloatI:
        """Convert to percentage."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "to_pct"))

    def to_dec(self) -> FloatI:
        """Convert to decimal."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "to_dec"))

    def to_int(self) -> IntI:
        """Get raw basis points."""
        from nu.terms import MethodCall
        from nu.primitives import IntI

        return IntI(MethodCall(self, "to_int"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Nu) -> FloatI:
        """Apply basis points to amount."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "apply", amount))

    def add_to(self, amount: int | float | Nu) -> FloatI:
        """Add basis points to amount."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "add_to", amount))

    def sub_from(self, amount: int | float | Nu) -> FloatI:
        """Subtract basis points from amount."""
        from nu.terms import MethodCall
        from nu.primitives import FloatI

        return FloatI(MethodCall(self, "sub_from", amount))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: BasisPointArg) -> BasisPointI:
        """Add basis points."""
        from nu import Add

        if isinstance(other, BasisPoint):
            other = BasisPointI(other)
        return BasisPointI(Add(self, other))

    def __radd__(self, other: BasisPoint | int) -> BasisPointI:
        """Right add."""
        from nu import Add

        if isinstance(other, BasisPoint):
            other = BasisPointI(other)
        return BasisPointI(Add(other, self))

    def __sub__(self, other: BasisPointArg) -> BasisPointI:
        """Subtract basis points."""
        from nu import Sub

        if isinstance(other, BasisPoint):
            other = BasisPointI(other)
        return BasisPointI(Sub(self, other))

    def __rsub__(self, other: BasisPoint | int) -> BasisPointI:
        """Right subtract."""
        from nu import Sub

        if isinstance(other, BasisPoint):
            other = BasisPointI(other)
        return BasisPointI(Sub(other, self))

    def __mul__(self, factor: int | float | Nu) -> BasisPointI:
        """Multiply by factor."""
        from nu import Mul

        return BasisPointI(Mul(self, factor))

    def __rmul__(self, factor: int | float) -> BasisPointI:
        """Right multiply."""
        from nu import Mul

        return BasisPointI(Mul(factor, self))

    def __truediv__(self, divisor: int | float | Nu) -> BasisPointI:
        """Divide by factor."""
        from nu import Div

        return BasisPointI(Div(self, divisor))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: BasisPointArg) -> BoolI:
        """Greater than."""
        from nu import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: BasisPointArg) -> BoolI:
        """Less than."""
        from nu import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: BasisPointArg) -> BoolI:
        """Greater than or equal."""
        from nu import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: BasisPointArg) -> BoolI:
        """Less than or equal."""
        from nu import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: BasisPointArg) -> BoolI:
        """Equal."""
        from nu import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: BasisPointArg) -> BoolI:
        """Not equal."""
        from nu import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))


class BasisPointI(_BasisPointI, TypedNu[BasisPoint]):
    """Computed BasisPoint value."""

    pass
