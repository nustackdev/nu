"""Decimal ref base for arbitrary precision decimal arithmetic.

DecimalRefBase = RefBase[Decimal] + Comparable + arithmetic operations.
Returns concrete py types (DecimalRef, IntRef, BoolRef).
"""

from __future__ import annotations

from abc import ABC
from decimal import Decimal
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef, IntRef

    from .args import DecimalArg
    from .py.refs import DecimalRef


__all__ = [
    "DecimalRefBase",
]


class DecimalRefBase(
    Comparable["Decimal | int | float | str | DecimalRef"],
    RefBase[Decimal],
    ABC,
):
    """Abstract base for Decimal refs.

    Provides arbitrary precision decimal arithmetic for financial
    and scientific calculations where floating point errors are unacceptable.

    Combines traits and returns concrete py types.
    """

    # =========================================================================
    # CONSTRUCTORS (class methods for creating refs)
    # =========================================================================

    @classmethod
    def from_str(cls, value: str | Term[str]) -> DecimalRef:
        """Create a DecimalRef from a string."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DecimalRef

        return DecimalRef(FuncCallOp(Decimal, value))

    @classmethod
    def from_int(cls, value: int | Term[int]) -> DecimalRef:
        """Create a DecimalRef from an integer."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DecimalRef

        return DecimalRef(FuncCallOp(Decimal, value))

    @classmethod
    def from_float(cls, value: float | Term[float]) -> DecimalRef:
        """Create a DecimalRef from a float.

        Note: Converting from float may introduce precision issues.
        Prefer from_str() for exact values.
        """
        from everybase.morphisms import FuncCallOp

        from .py.refs import DecimalRef

        return DecimalRef(FuncCallOp(Decimal, value))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: DecimalArg) -> DecimalRef:
        """Add two decimals."""
        from everybase.morphisms import AddOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(AddOp(self, other))

    def __radd__(self, other: Decimal | int | float | str) -> DecimalRef:
        """Right add."""
        from everybase.morphisms import AddOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(AddOp(other, self))

    def __sub__(self, other: DecimalArg) -> DecimalRef:
        """Subtract decimals."""
        from everybase.morphisms import SubOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(SubOp(self, other))

    def __rsub__(self, other: Decimal | int | float | str) -> DecimalRef:
        """Right subtract."""
        from everybase.morphisms import SubOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(SubOp(other, self))

    def __mul__(self, other: DecimalArg) -> DecimalRef:
        """Multiply decimals."""
        from everybase.morphisms import MulOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(MulOp(self, other))

    def __rmul__(self, other: Decimal | int | float | str) -> DecimalRef:
        """Right multiply."""
        from everybase.morphisms import MulOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(MulOp(other, self))

    def __truediv__(self, other: DecimalArg) -> DecimalRef:
        """Divide decimals."""
        from everybase.morphisms import DivOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(DivOp(self, other))

    def __rtruediv__(self, other: Decimal | int | float | str) -> DecimalRef:
        """Right divide."""
        from everybase.morphisms import DivOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(DivOp(other, self))

    def __floordiv__(self, other: DecimalArg) -> DecimalRef:
        """Floor divide decimals."""
        from everybase.morphisms import FloorDivOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(FloorDivOp(self, other))

    def __mod__(self, other: DecimalArg) -> DecimalRef:
        """Modulo operation."""
        from everybase.morphisms import ModOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(ModOp(self, other))

    def __pow__(self, other: int | DecimalArg) -> DecimalRef:
        """Raise to power."""
        from everybase.morphisms import PowOp

        from .py.refs import DecimalRef

        if isinstance(other, Decimal):
            other = DecimalRef(other)
        return DecimalRef(PowOp(self, other))

    def __neg__(self) -> DecimalRef:
        """Negate."""
        from everybase.morphisms import NegOp

        from .py.refs import DecimalRef

        return DecimalRef(NegOp(self))

    def __abs__(self) -> DecimalRef:
        """Absolute value."""
        from everybase.morphisms import AbsOp

        from .py.refs import DecimalRef

        return DecimalRef(AbsOp(self))

    # =========================================================================
    # ROUNDING AND QUANTIZATION
    # =========================================================================

    def quantize(self, exp: str | DecimalArg, rounding: str | None = None) -> DecimalRef:
        """Quantize to a given exponent (e.g., "0.01" for 2 decimal places)."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DecimalRef

        if isinstance(exp, Decimal):
            exp = DecimalRef(exp)
        if rounding is not None:
            return DecimalRef(MethodCallOp(self, "quantize", exp, rounding))
        return DecimalRef(MethodCallOp(self, "quantize", exp))

    def normalize(self) -> DecimalRef:
        """Remove trailing zeros."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DecimalRef

        return DecimalRef(MethodCallOp(self, "normalize"))

    def sqrt(self) -> DecimalRef:
        """Square root."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DecimalRef

        return DecimalRef(MethodCallOp(self, "sqrt"))

    def exp(self) -> DecimalRef:
        """Exponential (e^self)."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DecimalRef

        return DecimalRef(MethodCallOp(self, "exp"))

    def ln(self) -> DecimalRef:
        """Natural logarithm."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DecimalRef

        return DecimalRef(MethodCallOp(self, "ln"))

    def log10(self) -> DecimalRef:
        """Base-10 logarithm."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DecimalRef

        return DecimalRef(MethodCallOp(self, "log10"))

    # =========================================================================
    # INSPECTION
    # =========================================================================

    def is_finite(self) -> BoolRef:
        """Check if value is finite."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_finite"))

    def is_infinite(self) -> BoolRef:
        """Check if value is infinite."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_infinite"))

    def is_signed(self) -> BoolRef:
        """Check if value is negative."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_signed"))

    def is_zero(self) -> BoolRef:
        """Check if value is zero."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_zero"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_int(self) -> IntRef:
        """Convert to integer (truncating decimal)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(int, self))
