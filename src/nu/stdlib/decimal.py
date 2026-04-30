"""DecimalI - arbitrary precision decimal interface.

DecimalI = TypedNu[Decimal] + arithmetic + comparison + rounding + inspection.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Form, Mode, TypedNu


if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.forms.primitives import BoolForm, IntForm

__all__ = [
    "DecimalArg",
    "DecimalI",
]

type DecimalArg = Arg[Decimal]


class _DecimalI(Form):
    """Mixin for Decimal operations.

    Provides arbitrary precision decimal arithmetic for financial
    and scientific calculations where floating point errors are unacceptable.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Nu[str]) -> DecimalI:
        """Create a DecimalI from a string."""
        from nu import FuncCall

        return DecimalI(FuncCall(Decimal, value))

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> DecimalI:
        """Create a DecimalI from an integer."""
        from nu import FuncCall

        return DecimalI(FuncCall(Decimal, value))

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> DecimalI:
        """Create a DecimalI from a float.

        Note: Converting from float may introduce precision issues.
        Prefer from_str() for exact values.
        """
        from nu import FuncCall

        return DecimalI(FuncCall(Decimal, value))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: DecimalArg) -> DecimalI:
        """Add two decimals."""
        from nu import Add

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Add(self, other))

    def __radd__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right add."""
        from nu import Add

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Add(other, self))

    def __sub__(self, other: DecimalArg) -> DecimalI:
        """Subtract decimals."""
        from nu import Sub

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Sub(self, other))

    def __rsub__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right subtract."""
        from nu import Sub

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Sub(other, self))

    def __mul__(self, other: DecimalArg) -> DecimalI:
        """Multiply decimals."""
        from nu import Mul

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Mul(self, other))

    def __rmul__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right multiply."""
        from nu import Mul

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Mul(other, self))

    def __truediv__(self, other: DecimalArg) -> DecimalI:
        """Divide decimals."""
        from nu import Div

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Div(self, other))

    def __rtruediv__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right divide."""
        from nu import Div

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Div(other, self))

    def __floordiv__(self, other: DecimalArg) -> DecimalI:
        """Floor divide decimals."""
        from nu import FloorDiv

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(FloorDiv(self, other))

    def __mod__(self, other: DecimalArg) -> DecimalI:
        """Modulo operation."""
        from nu import Mod

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Mod(self, other))

    def __pow__(self, other: int | DecimalArg) -> DecimalI:
        """Raise to power."""
        from nu import Pow

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(Pow(self, other))

    def __neg__(self) -> DecimalI:
        """Negate."""
        from nu import Neg

        return DecimalI(Neg(self))

    def __abs__(self) -> DecimalI:
        """Absolute value."""
        from nu import Abs

        return DecimalI(Abs(self))

    # =========================================================================
    # ROUNDING AND QUANTIZATION
    # =========================================================================

    def quantize(self, exp: str | DecimalArg, rounding: str | None = None) -> DecimalI:
        """Quantize to a given exponent (e.g., "0.01" for 2 decimal places)."""
        from nu import MethodCall

        if isinstance(exp, Decimal):
            exp = DecimalI(exp)
        if rounding is not None:
            return DecimalI(MethodCall(self, "quantize", exp, rounding))
        return DecimalI(MethodCall(self, "quantize", exp))

    def normalize(self) -> DecimalI:
        """Remove trailing zeros."""
        from nu import MethodCall

        return DecimalI(MethodCall(self, "normalize"))

    def sqrt(self) -> DecimalI:
        """Square root."""
        from nu import MethodCall

        return DecimalI(MethodCall(self, "sqrt"))

    def exp(self) -> DecimalI:
        """Exponential (e^self)."""
        from nu import MethodCall

        return DecimalI(MethodCall(self, "exp"))

    def ln(self) -> DecimalI:
        """Natural logarithm."""
        from nu import MethodCall

        return DecimalI(MethodCall(self, "ln"))

    def log10(self) -> DecimalI:
        """Base-10 logarithm."""
        from nu import MethodCall

        return DecimalI(MethodCall(self, "log10"))

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def is_finite(self) -> BoolForm:
        """Check if value is finite."""
        from nu import MethodCall
        from nu.forms.primitives import BoolForm

        return BoolForm(MethodCall(self, "is_finite"))

    def is_infinite(self) -> BoolForm:
        """Check if value is infinite."""
        from nu import MethodCall
        from nu.forms.primitives import BoolForm

        return BoolForm(MethodCall(self, "is_infinite"))

    def is_signed(self) -> BoolForm:
        """Check if value is negative."""
        from nu import MethodCall
        from nu.forms.primitives import BoolForm

        return BoolForm(MethodCall(self, "is_signed"))

    def is_zero(self) -> BoolForm:
        """Check if value is zero."""
        from nu import MethodCall
        from nu.forms.primitives import BoolForm

        return BoolForm(MethodCall(self, "is_zero"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntForm:
        """Convert to integer (truncating decimal)."""
        from nu import FuncCall
        from nu.forms.primitives import IntForm

        return IntForm(FuncCall(int, self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DecimalArg) -> BoolForm:
        """Greater than."""
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: DecimalArg) -> BoolForm:
        """Less than."""
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: DecimalArg) -> BoolForm:
        """Greater than or equal."""
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: DecimalArg) -> BoolForm:
        """Less than or equal."""
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: DecimalArg) -> BoolForm:
        """Equal."""
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: DecimalArg) -> BoolForm:
        """Not equal."""
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class DecimalI(_DecimalI, TypedNu[Decimal]):
    """Decimal interface. Arbitrary precision arithmetic + comparable."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
