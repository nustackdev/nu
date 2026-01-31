"""Basis point ref base for financial rate/fee representation.

BasisPointRefBase = RefBase[BasisPoint] + Comparable + arithmetic operations.
Basis point = 1/100th of a percent (500 bps = 5%).
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable

from .basis_point_cls import BasisPoint


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import FloatRef, IntRef

    from .args import BasisPointArg
    from .py.refs import BasisPointRef


__all__ = [
    "BasisPointRefBase",
]


class BasisPointRefBase(
    Comparable["BasisPoint | int | BasisPointRef"],
    RefBase[BasisPoint],
    ABC,
):
    """Abstract base for BasisPoint refs.

    Provides basis point operations for precise rate/fee representation.
    Stored as int (raw basis points) for serialization.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_int(cls, value: int | Term[int]) -> BasisPointRef:
        """Create from raw basis points."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import BasisPointRef

        return BasisPointRef(FuncCallOp(BasisPoint, value))

    @classmethod
    def from_pct(cls, pct: float | Term[float]) -> BasisPointRef:
        """Create from percentage."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import BasisPointRef

        return BasisPointRef(FuncCallOp(BasisPoint.from_pct, pct))

    @classmethod
    def from_dec(cls, dec: float | Term[float]) -> BasisPointRef:
        """Create from decimal."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import BasisPointRef

        return BasisPointRef(FuncCallOp(BasisPoint.from_dec, dec))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def to_pct(self) -> FloatRef:
        """Convert to percentage."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "to_pct"))

    def to_dec(self) -> FloatRef:
        """Convert to decimal."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "to_dec"))

    def to_int(self) -> IntRef:
        """Get raw basis points."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "to_int"))

    # =========================================================================
    # APPLICATION
    # =========================================================================

    def apply(self, amount: int | float | Term) -> FloatRef:
        """Apply basis points to amount."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "apply", amount))

    def add_to(self, amount: int | float | Term) -> FloatRef:
        """Add basis points to amount."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "add_to", amount))

    def sub_from(self, amount: int | float | Term) -> FloatRef:
        """Subtract basis points from amount."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "sub_from", amount))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: BasisPointArg) -> BasisPointRef:
        """Add basis points."""
        from everybase.morphisms import AddOp

        from .py.refs import BasisPointRef

        if isinstance(other, BasisPoint):
            other = BasisPointRef(other)
        return BasisPointRef(AddOp(self, other))

    def __radd__(self, other: BasisPoint | int) -> BasisPointRef:
        """Right add."""
        from everybase.morphisms import AddOp

        from .py.refs import BasisPointRef

        if isinstance(other, BasisPoint):
            other = BasisPointRef(other)
        return BasisPointRef(AddOp(other, self))

    def __sub__(self, other: BasisPointArg) -> BasisPointRef:
        """Subtract basis points."""
        from everybase.morphisms import SubOp

        from .py.refs import BasisPointRef

        if isinstance(other, BasisPoint):
            other = BasisPointRef(other)
        return BasisPointRef(SubOp(self, other))

    def __rsub__(self, other: BasisPoint | int) -> BasisPointRef:
        """Right subtract."""
        from everybase.morphisms import SubOp

        from .py.refs import BasisPointRef

        if isinstance(other, BasisPoint):
            other = BasisPointRef(other)
        return BasisPointRef(SubOp(other, self))

    def __mul__(self, factor: int | float | Term) -> BasisPointRef:
        """Multiply by factor."""
        from everybase.morphisms import MulOp

        from .py.refs import BasisPointRef

        return BasisPointRef(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> BasisPointRef:
        """Right multiply."""
        from everybase.morphisms import MulOp

        from .py.refs import BasisPointRef

        return BasisPointRef(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | Term) -> BasisPointRef:
        """Divide by factor."""
        from everybase.morphisms import DivOp

        from .py.refs import BasisPointRef

        return BasisPointRef(DivOp(self, divisor))
