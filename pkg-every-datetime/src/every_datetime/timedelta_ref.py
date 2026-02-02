"""Timedelta type for duration values.

Pattern:
    TimedeltaType = TypeBase[timedelta] + ComparableBase + arithmetic operations
    TimedeltaValue = ValueBase + TimedeltaType (computed results)
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from everyabc import Sentinel
from everybase import (
    ComparableBase,
    FloatValue,
    IntValue,
    TypeBase,
    ValueBase,
)


if TYPE_CHECKING:
    from everyabc import Term

    from .args import TimedeltaArg


__all__ = [
    "TimedeltaType",
    "TimedeltaValue",
]


class TimedeltaType(
    ComparableBase["timedelta | TimedeltaType"],
    TypeBase[timedelta | Sentinel],
):
    """Abstract type for timedelta operations.

    Supports comparison, arithmetic, and duration-specific methods.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_seconds(cls, seconds: float | Term[float]) -> TimedeltaValue:
        """Create a TimedeltaValue from seconds."""
        from everybase import FuncCallOp

        return TimedeltaValue(FuncCallOp(timedelta, seconds=seconds))

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
    ) -> TimedeltaValue:
        """Create a TimedeltaValue from time components."""
        from everybase import FuncCallOp

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

    def days(self) -> IntValue:
        """Get the days component (normalized)."""
        from everybase import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "days"))

    def seconds(self) -> IntValue:
        """Get the seconds component (0-86399)."""
        from everybase import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "seconds"))

    def microseconds(self) -> IntValue:
        """Get the microseconds component (0-999999)."""
        from everybase import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "microseconds"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def total_seconds(self) -> FloatValue:
        """Get total duration in seconds."""
        from everybase import MethodCallOp

        return FloatValue(MethodCallOp(self, "total_seconds"))

    def total_minutes(self) -> FloatValue:
        """Get total duration in minutes."""
        return self.total_seconds() / 60.0

    def total_hours(self) -> FloatValue:
        """Get total duration in hours."""
        return self.total_seconds() / 3600.0

    def total_days(self) -> FloatValue:
        """Get total duration in days."""
        return self.total_seconds() / 86400.0

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: TimedeltaArg) -> TimedeltaValue:
        """Add two timedeltas."""
        from everybase import AddOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(AddOp(self, other))

    def __radd__(self, other: timedelta) -> TimedeltaValue:
        """Right add."""
        from everybase import AddOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(AddOp(other, self))

    def __sub__(self, other: TimedeltaArg) -> TimedeltaValue:
        """Subtract timedeltas."""
        from everybase import SubOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(SubOp(self, other))

    def __rsub__(self, other: timedelta) -> TimedeltaValue:
        """Right subtract."""
        from everybase import SubOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(SubOp(other, self))

    def __mul__(self, factor: int | float | Term) -> TimedeltaValue:
        """Multiply timedelta by a scalar."""
        from everybase import MulOp

        return TimedeltaValue(MulOp(self, factor))

    def __rmul__(self, factor: int | float) -> TimedeltaValue:
        """Right multiply."""
        from everybase import MulOp

        return TimedeltaValue(MulOp(factor, self))

    def __truediv__(self, divisor: int | float | TimedeltaArg) -> TimedeltaValue | FloatValue:
        """Divide timedelta."""
        from everybase import DivOp

        if isinstance(divisor, timedelta):
            divisor = TimedeltaValue(divisor)
        if isinstance(divisor, TimedeltaType):
            return FloatValue(DivOp(self, divisor))
        return TimedeltaValue(DivOp(self, divisor))

    def __floordiv__(self, divisor: int | Term[int]) -> TimedeltaValue:
        """Floor divide timedelta by scalar."""
        from everybase import FloorDivOp

        return TimedeltaValue(FloorDivOp(self, divisor))

    def __mod__(self, other: TimedeltaArg) -> TimedeltaValue:
        """Modulo operation."""
        from everybase import ModOp

        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        return TimedeltaValue(ModOp(self, other))

    def __neg__(self) -> TimedeltaValue:
        """Negate."""
        from everybase import NegOp

        return TimedeltaValue(NegOp(self))

    def __abs__(self) -> TimedeltaValue:
        """Absolute value."""
        from everybase import AbsOp

        return TimedeltaValue(AbsOp(self))

    def __pos__(self) -> TimedeltaValue:
        """Unary positive (returns self)."""
        return self  # type: ignore[return-value]


# =============================================================================
# VALUE (computed results)
# =============================================================================


class TimedeltaValue(ValueBase, TimedeltaType):
    """Computed timedelta value (Python memory substrate)."""

    pass
