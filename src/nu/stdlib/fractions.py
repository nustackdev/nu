"""FractionI - exact rational arithmetic interface.

FractionI = TypedNu[Fraction] + arithmetic + comparison + conversions.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu

if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.collections import TupleI
    from nu.primitives import BoolI, FloatI, IntI

    from .decimal import DecimalArg

__all__ = [
    "FractionArg",
    "FractionI",
]

type FractionArg = Arg[Fraction]


class _FractionI(Interface):
    """Mixin for Fraction operations.

    Provides exact rational arithmetic.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        numerator: int | Nu[int],
        denominator: int | Nu[int] = 1,
    ) -> FractionI:
        """Create a FractionI from numerator and denominator."""
        from nu import FuncCallOp

        return FractionI(FuncCallOp(Fraction, numerator, denominator))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> FractionI:
        """Create a FractionI from a string."""
        from nu import FuncCallOp

        return FractionI(FuncCallOp(Fraction, value))

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> FractionI:
        """Create a FractionI from a float."""
        from nu import FuncCallOp

        return FractionI(FuncCallOp(Fraction, value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> FractionI:
        """Create a FractionI from a Decimal."""
        from nu import FuncCallOp

        return FractionI(FuncCallOp(Fraction, value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def numerator(self) -> IntI:
        """Get the numerator."""
        from nu import FuncCallOp
        from nu.primitives import IntI

        return IntI(FuncCallOp(getattr, self, "numerator"))

    def denominator(self) -> IntI:
        """Get the denominator."""
        from nu import FuncCallOp
        from nu.primitives import IntI

        return IntI(FuncCallOp(getattr, self, "denominator"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: FractionArg | int | float) -> FractionI:
        """Add fractions."""
        from nu import AddOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(AddOp(self, other))

    def __radd__(self, other: Fraction | int | float) -> FractionI:
        """Right add."""
        from nu import AddOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(AddOp(other, self))

    def __sub__(self, other: FractionArg | int | float) -> FractionI:
        """Subtract fractions."""
        from nu import SubOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(SubOp(self, other))

    def __rsub__(self, other: Fraction | int | float) -> FractionI:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(SubOp(other, self))

    def __mul__(self, other: FractionArg | int | float) -> FractionI:
        """Multiply fractions."""
        from nu import MulOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(MulOp(self, other))

    def __rmul__(self, other: Fraction | int | float) -> FractionI:
        """Right multiply."""
        from nu import MulOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(MulOp(other, self))

    def __truediv__(self, other: FractionArg | int | float) -> FractionI:
        """Divide fractions."""
        from nu import DivOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(DivOp(self, other))

    def __rtruediv__(self, other: Fraction | int | float) -> FractionI:
        """Right divide."""
        from nu import DivOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(DivOp(other, self))

    def __floordiv__(self, other: FractionArg | int | float) -> IntI:
        """Floor divide fractions."""
        from nu import FloorDivOp
        from nu.primitives import IntI

        if isinstance(other, Fraction):
            other = FractionI(other)
        return IntI(FloorDivOp(self, other))

    def __mod__(self, other: FractionArg | int | float) -> FractionI:
        """Modulo operation."""
        from nu import ModOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(ModOp(self, other))

    def __rfloordiv__(self, other: Fraction | int | float) -> IntI:
        """Right floor divide."""
        from nu import FloorDivOp
        from nu.primitives import IntI

        if isinstance(other, Fraction):
            other = FractionI(other)
        return IntI(FloorDivOp(other, self))

    def __rmod__(self, other: Fraction | int | float) -> FractionI:
        """Right modulo."""
        from nu import ModOp

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(ModOp(other, self))

    def __pow__(self, other: int) -> FractionI:
        """Raise to power."""
        from nu import PowOp

        return FractionI(PowOp(self, other))

    def __neg__(self) -> FractionI:
        """Negate."""
        from nu import NegOp

        return FractionI(NegOp(self))

    def __abs__(self) -> FractionI:
        """Absolute value."""
        from nu import AbsOp

        return FractionI(AbsOp(self))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def limit_denominator(self, max_denominator: int = 10**6) -> FractionI:
        """Find closest fraction with denominator at most max_denominator."""
        from nu import MethodCallOp

        return FractionI(MethodCallOp(self, "limit_denominator", max_denominator))

    def as_float(self) -> FloatI:
        """Convert to float."""
        from nu import FuncCallOp
        from nu.primitives import FloatI

        return FloatI(FuncCallOp(float, self))

    def as_integer_ratio(self) -> TupleI:
        """Return (numerator, denominator) tuple."""
        from nu import MethodCallOp
        from nu.collections import TupleI

        return TupleI(MethodCallOp(self, "as_integer_ratio"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FractionArg | int | float) -> BoolI:
        """Greater than."""
        from nu import GtOp
        from nu.primitives import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: FractionArg | int | float) -> BoolI:
        """Less than."""
        from nu import LtOp
        from nu.primitives import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: FractionArg | int | float) -> BoolI:
        """Greater than or equal."""
        from nu import GeOp
        from nu.primitives import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: FractionArg | int | float) -> BoolI:
        """Less than or equal."""
        from nu import LeOp
        from nu.primitives import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: FractionArg | int | float) -> BoolI:
        """Equal."""
        from nu import EqOp
        from nu.primitives import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: FractionArg | int | float) -> BoolI:
        """Not equal."""
        from nu import NeOp
        from nu.primitives import BoolI

        return BoolI(NeOp(self, other))


class FractionI(_FractionI, TypedNu[Fraction]):
    """Fraction interface. Exact rational arithmetic + comparable."""
