"""Percentage ref base for percentage values.

PercentageRefBase = RefBase[Percentage] + Comparable + arithmetic operations.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable

from .percentage_cls import Percentage


if TYPE_CHECKING:
    from every import Term
    from everybase.py import BoolRef, FloatRef, IntRef

    from .args import PercentageArg
    from .py.refs import PercentageRef


__all__ = [
    "PercentageRefBase",
]


class PercentageRefBase(
    Comparable["Percentage | float | PercentageRef"],
    RefBase[Percentage],
    ABC,
):
    """Abstract base for Percentage refs.

    Provides percentage operations. Stored as float for serialization.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_float(cls, value: float | Term[float]) -> PercentageRef:
        """Create from percentage float."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PercentageRef

        return PercentageRef(FuncCallOp(Percentage, value))

    @classmethod
    def from_dec(cls, dec: float | Term[float]) -> PercentageRef:
        """Create from decimal."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PercentageRef

        return PercentageRef(FuncCallOp(Percentage.from_dec, dec))

    @classmethod
    def from_bps(cls, bps: int | Term[int]) -> PercentageRef:
        """Create from basis points."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import PercentageRef

        return PercentageRef(FuncCallOp(Percentage.from_bps, bps))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_dec(self) -> FloatRef:
        """Convert to decimal."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "to_dec"))

    def to_bps(self) -> IntRef:
        """Convert to basis points."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "to_bps"))

    def to_float(self) -> FloatRef:
        """Get raw percentage."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "to_float"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Term) -> FloatRef:
        """Apply percentage to amount."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "apply", amount))

    def of(self, amount: int | float | Term) -> FloatRef:
        """Alias for apply."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "of", amount))

    def add_to(self, amount: int | float | Term) -> FloatRef:
        """Add percentage to amount."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: int | float | Term) -> FloatRef:
        """Subtract percentage from amount."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def is_valid(self, min_val: float = 0.0, max_val: float = 100.0) -> BoolRef:
        """Check if within range."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import BoolRef

        return BoolRef(MethodCallOp(self, "is_valid", min_val, max_val))

    def clamp(self, min_val: float = 0.0, max_val: float = 100.0) -> PercentageRef:
        """Clamp to range."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import PercentageRef

        return PercentageRef(MethodCallOp(self, "clamp", min_val, max_val))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: PercentageArg | float) -> PercentageRef:
        """Add percentages."""
        from everybase.morphisms import AddOp

        from .py.refs import PercentageRef

        if isinstance(other, Percentage):
            other = PercentageRef(other)
        return PercentageRef(AddOp(self, other))

    def __radd__(self, other: Percentage | float) -> PercentageRef:
        """Right add."""
        from everybase.morphisms import AddOp

        from .py.refs import PercentageRef

        if isinstance(other, Percentage):
            other = PercentageRef(other)
        return PercentageRef(AddOp(other, self))

    def __sub__(self, other: PercentageArg | float) -> PercentageRef:
        """Subtract percentages."""
        from everybase.morphisms import SubOp

        from .py.refs import PercentageRef

        if isinstance(other, Percentage):
            other = PercentageRef(other)
        return PercentageRef(SubOp(self, other))

    def __rsub__(self, other: Percentage | float) -> PercentageRef:
        """Right subtract."""
        from everybase.morphisms import SubOp

        from .py.refs import PercentageRef

        if isinstance(other, Percentage):
            other = PercentageRef(other)
        return PercentageRef(SubOp(other, self))

    def __mul__(self, factor: int | float | Term) -> PercentageRef:
        """Multiply by factor."""
        from everybase.morphisms import MulOp

        from .py.refs import PercentageRef

        return PercentageRef(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> PercentageRef:
        """Right multiply."""
        from everybase.morphisms import MulOp

        from .py.refs import PercentageRef

        return PercentageRef(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | Term) -> PercentageRef:
        """Divide by factor."""
        from everybase.morphisms import DivOp

        from .py.refs import PercentageRef

        return PercentageRef(DivOp(self, divisor))

    def __neg__(self) -> PercentageRef:
        """Negate."""
        from everybase.morphisms import NegOp

        from .py.refs import PercentageRef

        return PercentageRef(NegOp(self))
