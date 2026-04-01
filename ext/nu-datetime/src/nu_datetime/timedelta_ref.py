"""Timedelta type for duration values.

Pattern:
    TimedeltaType = Object[timedelta] + ComparableBase + arithmetic operations
    TimedeltaValue = Interface + TimedeltaType (computed results)
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    ComparableBase,
    FloatI,
    IntI,
    Object,
    Interface,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import TimedeltaArg


__all__ = [
    "TimedeltaType",
    "TimedeltaValue",
]


class TimedeltaType(
    ComparableBase["timedelta | TimedeltaType"],
    Object[timedelta | Sentinel],
):
    """Abstract type for timedelta operations.

    Supports comparison, arithmetic, and duration-specific methods.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_seconds(cls, seconds: float | Nu[float]) -> TimedeltaValue:
        """Create a TimedeltaValue from seconds."""
        from nu import FuncCallOp

        return TimedeltaValue(FuncCallOp(timedelta, seconds=seconds))

    @classmethod
    def from_components(
        cls,
        days: float | Nu[float] = 0,
        seconds: float | Nu[float] = 0,
        microseconds: float | Nu[float] = 0,
        milliseconds: float | Nu[float] = 0,
        minutes: float | Nu[float] = 0,
        hours: float | Nu[float] = 0,
        weeks: float | Nu[float] = 0,
    ) -> TimedeltaValue:
        """Create a TimedeltaValue from time components."""
        from nu import FuncCallOp

        return TimedeltaValue(
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

    def days(self) -> IntI:
        """Get the days component (normalized)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "days"))

    def seconds(self) -> IntI:
        """Get the seconds component (0-86399)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "seconds"))

    def microseconds(self) -> IntI:
        """Get the microseconds component (0-999999)."""
        from nu import FuncCallOp

        return IntI(FuncCallOp(getattr, self, "microseconds"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def total_seconds(self) -> FloatI:
        """Get total duration in seconds."""
        from nu import MethodCallOp

        return FloatI(MethodCallOp(self, "total_seconds"))

    def total_minutes(self) -> FloatI:
        """Get total duration in minutes."""
        return self.total_seconds() / 60.0

    def total_hours(self) -> FloatI:
        """Get total duration in hours."""
        return self.total_seconds() / 3600.0

    def total_days(self) -> FloatI:
        """Get total duration in days."""
        return self.total_seconds() / 86400.0

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: TimedeltaArg) -> TimedeltaValue:
        """Add two timedeltas."""
        from nu import AddOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(AddOp(self, other))

    def __radd__(self, other: timedelta) -> TimedeltaValue:
        """Right add."""
        from nu import AddOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(AddOp(other, self))

    def __sub__(self, other: TimedeltaArg) -> TimedeltaValue:
        """Subtract timedeltas."""
        from nu import SubOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(SubOp(self, other))

    def __rsub__(self, other: timedelta) -> TimedeltaValue:
        """Right subtract."""
        from nu import SubOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(SubOp(other, self))

    def __mul__(self, factor: int | float | Nu) -> TimedeltaValue:
        """Multiply timedelta by a scalar."""
        from nu import MulOp

        return TimedeltaValue(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> TimedeltaValue:
        """Right multiply."""
        from nu import MulOp

        return TimedeltaValue(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | TimedeltaArg) -> TimedeltaValue | FloatI:
        """Divide timedelta."""
        from nu import DivOp

        if isinstance(divisor, timedelta):
            divisor = TimedeltaValue(divisor)
        if isinstance(divisor, TimedeltaType):
            return FloatI(DivOp(self, divisor))
        return TimedeltaValue(DivOp(self, divisor))

    def __floordiv__(self, divisor: int | Nu[int]) -> TimedeltaValue:
        """Floor divide timedelta by scalar."""
        from nu import FloorDivOp

        return TimedeltaValue(FloorDivOp(self, divisor))

    def __mod__(self, other: TimedeltaArg) -> TimedeltaValue:
        """Modulo operation."""
        from nu import ModOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(ModOp(self, other))

    def __neg__(self) -> TimedeltaValue:
        """Negate."""
        from nu import NegOp

        return TimedeltaValue(NegOp(self))

    def __abs__(self) -> TimedeltaValue:
        """Absolute value."""
        from nu import AbsOp

        return TimedeltaValue(AbsOp(self))

    def __pos__(self) -> TimedeltaValue:
        """Unary positive (returns self)."""
        return self  # type: ignore[return-value]


# =============================================================================
# VALUE (computed results)
# =============================================================================


class TimedeltaValue(Interface, TimedeltaType):
    """Computed timedelta value (Python memory substrate)."""

    pass
