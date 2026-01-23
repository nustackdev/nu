"""Fraction ref base for exact rational arithmetic.

FractionRefBase = RefBase[Fraction] + Comparable + arithmetic operations.
Returns concrete py types (FractionRef, IntRef, FloatRef).
"""

from __future__ import annotations

from abc import ABC
from fractions import Fraction
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from every import Term
    from everybase.py import FloatRef, IntRef, TupleRef

    from .args import DecimalArg, FractionArg
    from .py.refs import FractionRef


__all__ = [
    "FractionRefBase",
]


class FractionRefBase(
    Comparable["Fraction | int | float | FractionRef"],
    RefBase[Fraction],
    ABC,
):
    """Abstract base for Fraction refs.

    Provides exact rational arithmetic. Stored as "numerator/denominator"
    string for serialization.

    Combines traits and returns concrete py types.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_components(
        cls,
        numerator: int | Term[int],
        denominator: int | Term[int] = 1,
    ) -> FractionRef:
        """Create a FractionRef from numerator and denominator."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import FractionRef

        return FractionRef(FuncCallOp(Fraction, numerator, denominator))

    @classmethod
    def from_str(cls, value: str | Term[str]) -> FractionRef:
        """Create a FractionRef from a string."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import FractionRef

        return FractionRef(FuncCallOp(Fraction, value))

    @classmethod
    def from_float(cls, value: float | Term[float]) -> FractionRef:
        """Create a FractionRef from a float."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import FractionRef

        return FractionRef(FuncCallOp(Fraction, value))

    @classmethod
    def from_decimal(cls, value: DecimalArg) -> FractionRef:
        """Create a FractionRef from a Decimal."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import FractionRef

        return FractionRef(FuncCallOp(Fraction, value))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def numerator(self) -> IntRef:
        """Get the numerator."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "numerator"))

    def denominator(self) -> IntRef:
        """Get the denominator."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "denominator"))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: FractionArg | int | float) -> FractionRef:
        """Add fractions."""
        from everybase.morphisms import AddOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(AddOp(self, other))

    def __radd__(self, other: Fraction | int | float) -> FractionRef:
        """Right add."""
        from everybase.morphisms import AddOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(AddOp(other, self))

    def __sub__(self, other: FractionArg | int | float) -> FractionRef:
        """Subtract fractions."""
        from everybase.morphisms import SubOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(SubOp(self, other))

    def __rsub__(self, other: Fraction | int | float) -> FractionRef:
        """Right subtract."""
        from everybase.morphisms import SubOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(SubOp(other, self))

    def __mul__(self, other: FractionArg | int | float) -> FractionRef:
        """Multiply fractions."""
        from everybase.morphisms import MulOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(MulOp(self, other))

    def __rmul__(self, other: Fraction | int | float) -> FractionRef:
        """Right multiply."""
        from everybase.morphisms import MulOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(MulOp(other, self))

    def __truediv__(self, other: FractionArg | int | float) -> FractionRef:
        """Divide fractions."""
        from everybase.morphisms import DivOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(DivOp(self, other))

    def __rtruediv__(self, other: Fraction | int | float) -> FractionRef:
        """Right divide."""
        from everybase.morphisms import DivOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(DivOp(other, self))

    def __floordiv__(self, other: FractionArg | int | float) -> IntRef:
        """Floor divide fractions."""
        from everybase.morphisms import FloorDivOp
        from everybase.py import IntRef

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return IntRef(FloorDivOp(self, other))

    def __mod__(self, other: FractionArg | int | float) -> FractionRef:
        """Modulo operation."""
        from everybase.morphisms import ModOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(ModOp(self, other))

    def __rfloordiv__(self, other: Fraction | int | float) -> IntRef:
        """Right floor divide."""
        from everybase.morphisms import FloorDivOp
        from everybase.py import IntRef

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return IntRef(FloorDivOp(other, self))

    def __rmod__(self, other: Fraction | int | float) -> FractionRef:
        """Right modulo."""
        from everybase.morphisms import ModOp

        from .py.refs import FractionRef

        if isinstance(other, Fraction):
            other = FractionRef(other)
        return FractionRef(ModOp(other, self))

    def __pow__(self, other: int) -> FractionRef:
        """Raise to power."""
        from everybase.morphisms import PowOp

        from .py.refs import FractionRef

        return FractionRef(PowOp(self, other))

    def __neg__(self) -> FractionRef:
        """Negate."""
        from everybase.morphisms import NegOp

        from .py.refs import FractionRef

        return FractionRef(NegOp(self))

    def __abs__(self) -> FractionRef:
        """Absolute value."""
        from everybase.morphisms import AbsOp

        from .py.refs import FractionRef

        return FractionRef(AbsOp(self))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def limit_denominator(self, max_denominator: int = 10**6) -> FractionRef:
        """Find closest fraction with denominator at most max_denominator."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import FractionRef

        return FractionRef(MethodCallOp(self, "limit_denominator", max_denominator))

    def as_float(self) -> FloatRef:
        """Convert to float."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import FloatRef

        return FloatRef(FuncCallOp(float, self))

    def as_integer_ratio(self) -> TupleRef:
        """Return (numerator, denominator) tuple."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import TupleRef

        return TupleRef(MethodCallOp(self, "as_integer_ratio"))
