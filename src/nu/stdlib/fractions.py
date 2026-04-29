"""FractionI - exact rational arithmetic interface.

FractionI = TypedNu[Fraction] + arithmetic + comparison + conversions.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Interface, Mode, TypedNu


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
        from nu import FuncCall

        return FractionI(FuncCall(Fraction, numerator, denominator))

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> FractionI:
        """Create a FractionI from a string."""
        from nu import FuncCall

        return FractionI(FuncCall(Fraction, value))

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> FractionI:
        """Create a FractionI from a float."""
        from nu import FuncCall

        return FractionI(FuncCall(Fraction, value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> FractionI:
        """Create a FractionI from a Decimal."""
        from nu import FuncCall

        return FractionI(FuncCall(Fraction, value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def numerator(self) -> IntI:
        """Get the numerator."""
        from nu import FuncCall
        from nu.primitives import IntI

        return IntI(FuncCall(getattr, self, "numerator"))

    def denominator(self) -> IntI:
        """Get the denominator."""
        from nu import FuncCall
        from nu.primitives import IntI

        return IntI(FuncCall(getattr, self, "denominator"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: FractionArg | int | float) -> FractionI:
        """Add fractions."""
        from nu import Add

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Add(self, other))

    def __radd__(self, other: Fraction | int | float) -> FractionI:
        """Right add."""
        from nu import Add

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Add(other, self))

    def __sub__(self, other: FractionArg | int | float) -> FractionI:
        """Subtract fractions."""
        from nu import Sub

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Sub(self, other))

    def __rsub__(self, other: Fraction | int | float) -> FractionI:
        """Right subtract."""
        from nu import Sub

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Sub(other, self))

    def __mul__(self, other: FractionArg | int | float) -> FractionI:
        """Multiply fractions."""
        from nu import Mul

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Mul(self, other))

    def __rmul__(self, other: Fraction | int | float) -> FractionI:
        """Right multiply."""
        from nu import Mul

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Mul(other, self))

    def __truediv__(self, other: FractionArg | int | float) -> FractionI:
        """Divide fractions."""
        from nu import Div

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Div(self, other))

    def __rtruediv__(self, other: Fraction | int | float) -> FractionI:
        """Right divide."""
        from nu import Div

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Div(other, self))

    def __floordiv__(self, other: FractionArg | int | float) -> IntI:
        """Floor divide fractions."""
        from nu import FloorDiv
        from nu.primitives import IntI

        if isinstance(other, Fraction):
            other = FractionI(other)
        return IntI(FloorDiv(self, other))

    def __mod__(self, other: FractionArg | int | float) -> FractionI:
        """Modulo operation."""
        from nu import Mod

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Mod(self, other))

    def __rfloordiv__(self, other: Fraction | int | float) -> IntI:
        """Right floor divide."""
        from nu import FloorDiv
        from nu.primitives import IntI

        if isinstance(other, Fraction):
            other = FractionI(other)
        return IntI(FloorDiv(other, self))

    def __rmod__(self, other: Fraction | int | float) -> FractionI:
        """Right modulo."""
        from nu import Mod

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Mod(other, self))

    def __pow__(self, other: int) -> FractionI:
        """Raise to power."""
        from nu import Pow

        return FractionI(Pow(self, other))

    def __neg__(self) -> FractionI:
        """Negate."""
        from nu import Neg

        return FractionI(Neg(self))

    def __abs__(self) -> FractionI:
        """Absolute value."""
        from nu import Abs

        return FractionI(Abs(self))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def limit_denominator(self, max_denominator: int = 10**6) -> FractionI:
        """Find closest fraction with denominator at most max_denominator."""
        from nu import MethodCall

        return FractionI(MethodCall(self, "limit_denominator", max_denominator))

    def as_float(self) -> FloatI:
        """Convert to float."""
        from nu import FuncCall
        from nu.primitives import FloatI

        return FloatI(FuncCall(float, self))

    def as_integer_ratio(self) -> TupleI:
        """Return (numerator, denominator) tuple."""
        from nu import MethodCall
        from nu.collections import TupleI

        return TupleI(MethodCall(self, "as_integer_ratio"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FractionArg | int | float) -> BoolI:
        """Greater than."""
        from nu import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: FractionArg | int | float) -> BoolI:
        """Less than."""
        from nu import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: FractionArg | int | float) -> BoolI:
        """Greater than or equal."""
        from nu import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: FractionArg | int | float) -> BoolI:
        """Less than or equal."""
        from nu import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: FractionArg | int | float) -> BoolI:
        """Equal."""
        from nu import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: FractionArg | int | float) -> BoolI:
        """Not equal."""
        from nu import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))


class FractionI(_FractionI, TypedNu[Fraction]):
    """Fraction interface. Exact rational arithmetic + comparable."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
