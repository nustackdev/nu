"""Timedelta ref base for duration values.

TimedeltaRefBase = RefBase[timedelta] + Comparable + arithmetic operations.
Stored as float (total_seconds) for serialization.
"""

from __future__ import annotations

from abc import ABC
from datetime import timedelta
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import FloatRef, IntRef

    from .args import TimedeltaArg
    from .py.refs import TimedeltaRef


__all__ = [
    "TimedeltaRefBase",
]


class TimedeltaRefBase(
    Comparable["timedelta | TimedeltaRef"],
    RefBase[timedelta],
    ABC,
):
    """Abstract base for timedelta refs.

    Supports comparison, arithmetic, and duration-specific methods.
    Stored as total seconds (float) for serialization.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_seconds(cls, seconds: float | Term[float]) -> TimedeltaRef:
        """Create a TimedeltaRef from seconds."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(FuncCallOp(timedelta, seconds=seconds))

    @classmethod
    def from_components(
        cls,
        days: float | Term[float] = 0,
        seconds: float | Term[float] = 0,
        microseconds: float | Term[float] = 0,
        milliseconds: float | Term[float] = 0,
        minutes: float | Term[float] = 0,
        hours: float | Term[float] = 0,
        weeks: float | Term[float] = 0,
    ) -> TimedeltaRef:
        """Create a TimedeltaRef from time components."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(
            FuncCallOp(
                timedelta,
                days=days,
                seconds=seconds,
                microseconds=microseconds,
                milliseconds=milliseconds,
                minutes=minutes,
                hours=hours,
                weeks=weeks,
            )
        )

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def days(self) -> IntRef:
        """Get the days component (normalized)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "days"))

    def seconds(self) -> IntRef:
        """Get the seconds component (0-86399)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "seconds"))

    def microseconds(self) -> IntRef:
        """Get the microseconds component (0-999999)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "microseconds"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def total_seconds(self) -> FloatRef:
        """Get total duration in seconds."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "total_seconds"))

    def total_minutes(self) -> FloatRef:
        """Get total duration in minutes."""
        return self.total_seconds() / 60.0

    def total_hours(self) -> FloatRef:
        """Get total duration in hours."""
        return self.total_seconds() / 3600.0

    def total_days(self) -> FloatRef:
        """Get total duration in days."""
        return self.total_seconds() / 86400.0

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: TimedeltaArg) -> TimedeltaRef:
        """Add two timedeltas."""
        from everybase.morphisms import AddOp

        from .py.refs import TimedeltaRef

        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        return TimedeltaRef(AddOp(self, other))

    def __radd__(self, other: timedelta) -> TimedeltaRef:
        """Right add."""
        from everybase.morphisms import AddOp

        from .py.refs import TimedeltaRef

        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        return TimedeltaRef(AddOp(other, self))

    def __sub__(self, other: TimedeltaArg) -> TimedeltaRef:
        """Subtract timedeltas."""
        from everybase.morphisms import SubOp

        from .py.refs import TimedeltaRef

        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        return TimedeltaRef(SubOp(self, other))

    def __rsub__(self, other: timedelta) -> TimedeltaRef:
        """Right subtract."""
        from everybase.morphisms import SubOp

        from .py.refs import TimedeltaRef

        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        return TimedeltaRef(SubOp(other, self))

    def __mul__(self, factor: int | float | Term) -> TimedeltaRef:
        """Multiply timedelta by a scalar."""
        from everybase.morphisms import MulOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> TimedeltaRef:
        """Right multiply."""
        from everybase.morphisms import MulOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | TimedeltaArg) -> TimedeltaRef | FloatRef:
        """Divide timedelta."""
        from everybase.morphisms import DivOp
        from everybase.py import FloatRef

        from .py.refs import TimedeltaRef

        if isinstance(divisor, timedelta):
            divisor = TimedeltaRef(divisor)
        if isinstance(divisor, TimedeltaRef):
            return FloatRef(DivOp(self, divisor))
        return TimedeltaRef(DivOp(self, divisor))

    def __floordiv__(self, divisor: int | Term[int]) -> TimedeltaRef:
        """Floor divide timedelta by scalar."""
        from everybase.morphisms import FloorDivOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(FloorDivOp(self, divisor))

    def __mod__(self, other: TimedeltaArg) -> TimedeltaRef:
        """Modulo operation."""
        from everybase.morphisms import ModOp

        from .py.refs import TimedeltaRef

        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        return TimedeltaRef(ModOp(self, other))

    def __neg__(self) -> TimedeltaRef:
        """Negate."""
        from everybase.morphisms import NegOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(NegOp(self))

    def __abs__(self) -> TimedeltaRef:
        """Absolute value."""
        from everybase.morphisms import AbsOp

        from .py.refs import TimedeltaRef

        return TimedeltaRef(AbsOp(self))

    def __pos__(self) -> TimedeltaRef:
        """Unary positive (returns self)."""
        return self
