"""DecimalI - arbitrary precision decimal interface.

DecimalI = TypedNu[Decimal] + arithmetic + comparison + rounding + inspection.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu

if TYPE_CHECKING:
    from nu import Arg, Nu
    from nu.primitives import BoolI, IntI

__all__ = [
    "DecimalArg",
    "DecimalI",
]

type DecimalArg = Arg[Decimal]


class _DecimalI(Interface):
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
        from nu import FuncCallOp

        return DecimalI(FuncCallOp(Decimal, value))

    @classmethod
    def from_int(cls, value: int | Nu[int]) -> DecimalI:
        """Create a DecimalI from an integer."""
        from nu import FuncCallOp

        return DecimalI(FuncCallOp(Decimal, value))

    @classmethod
    def from_float(cls, value: float | Nu[float]) -> DecimalI:
        """Create a DecimalI from a float.

        Note: Converting from float may introduce precision issues.
        Prefer from_str() for exact values.
        """
        from nu import FuncCallOp

        return DecimalI(FuncCallOp(Decimal, value))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: DecimalArg) -> DecimalI:
        """Add two decimals."""
        from nu import AddOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(AddOp(self, other))

    def __radd__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right add."""
        from nu import AddOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(AddOp(other, self))

    def __sub__(self, other: DecimalArg) -> DecimalI:
        """Subtract decimals."""
        from nu import SubOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(SubOp(self, other))

    def __rsub__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(SubOp(other, self))

    def __mul__(self, other: DecimalArg) -> DecimalI:
        """Multiply decimals."""
        from nu import MulOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(MulOp(self, other))

    def __rmul__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right multiply."""
        from nu import MulOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(MulOp(other, self))

    def __truediv__(self, other: DecimalArg) -> DecimalI:
        """Divide decimals."""
        from nu import DivOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(DivOp(self, other))

    def __rtruediv__(self, other: Decimal | int | float | str) -> DecimalI:
        """Right divide."""
        from nu import DivOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(DivOp(other, self))

    def __floordiv__(self, other: DecimalArg) -> DecimalI:
        """Floor divide decimals."""
        from nu import FloorDivOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(FloorDivOp(self, other))

    def __mod__(self, other: DecimalArg) -> DecimalI:
        """Modulo operation."""
        from nu import ModOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(ModOp(self, other))

    def __pow__(self, other: int | DecimalArg) -> DecimalI:
        """Raise to power."""
        from nu import PowOp

        if isinstance(other, Decimal):
            other = DecimalI(other)
        return DecimalI(PowOp(self, other))

    def __neg__(self) -> DecimalI:
        """Negate."""
        from nu import NegOp

        return DecimalI(NegOp(self))

    def __abs__(self) -> DecimalI:
        """Absolute value."""
        from nu import AbsOp

        return DecimalI(AbsOp(self))

    # =========================================================================
    # ROUNDING AND QUANTIZATION
    # =========================================================================

    def quantize(self, exp: str | DecimalArg, rounding: str | None = None) -> DecimalI:
        """Quantize to a given exponent (e.g., "0.01" for 2 decimal places)."""
        from nu import MethodCallOp

        if isinstance(exp, Decimal):
            exp = DecimalI(exp)
        if rounding is not None:
            return DecimalI(MethodCallOp(self, "quantize", exp, rounding))
        return DecimalI(MethodCallOp(self, "quantize", exp))

    def normalize(self) -> DecimalI:
        """Remove trailing zeros."""
        from nu import MethodCallOp

        return DecimalI(MethodCallOp(self, "normalize"))

    def sqrt(self) -> DecimalI:
        """Square root."""
        from nu import MethodCallOp

        return DecimalI(MethodCallOp(self, "sqrt"))

    def exp(self) -> DecimalI:
        """Exponential (e^self)."""
        from nu import MethodCallOp

        return DecimalI(MethodCallOp(self, "exp"))

    def ln(self) -> DecimalI:
        """Natural logarithm."""
        from nu import MethodCallOp

        return DecimalI(MethodCallOp(self, "ln"))

    def log10(self) -> DecimalI:
        """Base-10 logarithm."""
        from nu import MethodCallOp

        return DecimalI(MethodCallOp(self, "log10"))

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def is_finite(self) -> BoolI:
        """Check if value is finite."""
        from nu import MethodCallOp
        from nu.primitives import BoolI

        return BoolI(MethodCallOp(self, "is_finite"))

    def is_infinite(self) -> BoolI:
        """Check if value is infinite."""
        from nu import MethodCallOp
        from nu.primitives import BoolI

        return BoolI(MethodCallOp(self, "is_infinite"))

    def is_signed(self) -> BoolI:
        """Check if value is negative."""
        from nu import MethodCallOp
        from nu.primitives import BoolI

        return BoolI(MethodCallOp(self, "is_signed"))

    def is_zero(self) -> BoolI:
        """Check if value is zero."""
        from nu import MethodCallOp
        from nu.primitives import BoolI

        return BoolI(MethodCallOp(self, "is_zero"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntI:
        """Convert to integer (truncating decimal)."""
        from nu import FuncCallOp
        from nu.primitives import IntI

        return IntI(FuncCallOp(int, self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DecimalArg) -> BoolI:
        """Greater than."""
        from nu import GtOp
        from nu.primitives import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: DecimalArg) -> BoolI:
        """Less than."""
        from nu import LtOp
        from nu.primitives import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: DecimalArg) -> BoolI:
        """Greater than or equal."""
        from nu import GeOp
        from nu.primitives import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: DecimalArg) -> BoolI:
        """Less than or equal."""
        from nu import LeOp
        from nu.primitives import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: DecimalArg) -> BoolI:
        """Equal."""
        from nu import EqOp
        from nu.primitives import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: DecimalArg) -> BoolI:
        """Not equal."""
        from nu import NeOp
        from nu.primitives import BoolI

        return BoolI(NeOp(self, other))


class DecimalI(_DecimalI, TypedNu[Decimal]):
    """Decimal interface. Arbitrary precision arithmetic + comparable."""
