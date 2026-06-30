"""FractionI - exact rational arithmetic interface.

FractionI = TypedNu[Fraction] + arithmetic + comparison + conversions.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Form, Mode, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.forms.collections import TupleForm
    from nu.forms.primitives import BoolForm, FloatForm, IntForm

    from .decimal import DecimalArg

__all__ = [
    "FractionArg",
    "FractionI",
]

type FractionArg = Arg[Fraction]


class _FractionI(Form):
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

    def numerator(self) -> IntForm:
        """Get the numerator."""
        from nu import FuncCall
        from nu.forms.primitives import IntForm

        return IntForm(FuncCall(getattr, self, "numerator"))

    def denominator(self) -> IntForm:
        """Get the denominator."""
        from nu import FuncCall
        from nu.forms.primitives import IntForm

        return IntForm(FuncCall(getattr, self, "denominator"))

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

    def __floordiv__(self, other: FractionArg | int | float) -> IntForm:
        """Floor divide fractions."""
        from nu import FloorDiv
        from nu.forms.primitives import IntForm

        if isinstance(other, Fraction):
            other = FractionI(other)
        return IntForm(FloorDiv(self, other))

    def __mod__(self, other: FractionArg | int | float) -> FractionI:
        """Modulo operation."""
        from nu import Mod

        if isinstance(other, Fraction):
            other = FractionI(other)
        return FractionI(Mod(self, other))

    def __rfloordiv__(self, other: Fraction | int | float) -> IntForm:
        """Right floor divide."""
        from nu import FloorDiv
        from nu.forms.primitives import IntForm

        if isinstance(other, Fraction):
            other = FractionI(other)
        return IntForm(FloorDiv(other, self))

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

    def as_float(self) -> FloatForm:
        """Convert to float."""
        from nu import FuncCall
        from nu.forms.primitives import FloatForm

        return FloatForm(FuncCall(float, self))

    def as_integer_ratio(self) -> TupleForm:
        """Return (numerator, denominator) tuple."""
        from nu import MethodCall
        from nu.forms.collections import TupleForm

        return TupleForm(MethodCall(self, "as_integer_ratio"))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FractionArg | int | float) -> BoolForm:
        """Greater than."""
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: FractionArg | int | float) -> BoolForm:
        """Less than."""
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: FractionArg | int | float) -> BoolForm:
        """Greater than or equal."""
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: FractionArg | int | float) -> BoolForm:
        """Less than or equal."""
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: FractionArg | int | float) -> BoolForm:
        """Equal."""
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: FractionArg | int | float) -> BoolForm:
        """Not equal."""
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class FractionI(_FractionI, TypedNu[Fraction]):
    """Fraction interface. Exact rational arithmetic + comparable."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
