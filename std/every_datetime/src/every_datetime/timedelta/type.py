"""Timedelta Type."""

from __future__ import annotations

from datetime import timedelta

from term.ops import AddOp, DivOp, FloorDivOp, FuncCallOp, MethodCallOp, ModOp, MulOp, SubOp
from term.types import BaseType, ComparisonBase, FloatType, IntType, NegatableBase
from term.typing import Sentinel

from every._abc import FloatArg, IntArg, Term

from .args import TimedeltaArg


__all__ = [
    "TimedeltaType",
]


class TimedeltaType(
    ComparisonBase["timedelta | TimedeltaType"],
    NegatableBase["TimedeltaType"],
    BaseType[timedelta | Sentinel],
):
    """Type representing a timedelta.

    Supports comparison, arithmetic, and duration-specific methods.
    Stored as total seconds (float) for serialization.

    Example:
        >>> td = TimedeltaType.from_seconds(3600)
        >>> td.total_seconds()  # FloatType
        >>> td.days()  # IntType
        >>> td * 2  # TimedeltaType
        >>> td > other_td  # BoolType
    """

    def _wrap_arithmetic_result(self, operand: Term) -> Term:
        return TimedeltaType(operand)

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_seconds(cls, seconds: FloatArg) -> TimedeltaType:
        """Create a TimedeltaType from seconds."""
        return cls(FuncCallOp(timedelta, seconds=seconds))

    @classmethod
    def from_components(
        cls,
        days: FloatArg = 0,
        seconds: FloatArg = 0,
        microseconds: FloatArg = 0,
        milliseconds: FloatArg = 0,
        minutes: FloatArg = 0,
        hours: FloatArg = 0,
        weeks: FloatArg = 0,
    ) -> TimedeltaType:
        """Create a TimedeltaType from time components."""
        return cls(
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

    def days(self) -> IntType:
        """Get the days component (normalized)."""
        return IntType(FuncCallOp(getattr, self, "days"))

    def seconds(self) -> IntType:
        """Get the seconds component (0-86399)."""
        return IntType(FuncCallOp(getattr, self, "seconds"))

    def microseconds(self) -> IntType:
        """Get the microseconds component (0-999999)."""
        return IntType(FuncCallOp(getattr, self, "microseconds"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def total_seconds(self) -> FloatType:
        """Get total duration in seconds."""
        return FloatType(MethodCallOp(self, "total_seconds"))

    def total_minutes(self) -> FloatType:
        """Get total duration in minutes."""
        return self.total_seconds() / 60.0

    def total_hours(self) -> FloatType:
        """Get total duration in hours."""
        return self.total_seconds() / 3600.0

    def total_days(self) -> FloatType:
        """Get total duration in days."""
        return self.total_seconds() / 86400.0

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: TimedeltaArg) -> TimedeltaType:
        """Add two timedeltas."""
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        return TimedeltaType(AddOp(self, other))

    def __radd__(self, other: TimedeltaArg) -> TimedeltaType:
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        return TimedeltaType(AddOp(other, self))

    def __sub__(self, other: TimedeltaArg) -> TimedeltaType:
        """Subtract timedeltas."""
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        return TimedeltaType(SubOp(self, other))

    def __rsub__(self, other: TimedeltaArg) -> TimedeltaType:
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        return TimedeltaType(SubOp(other, self))

    def __mul__(self, factor: IntArg | FloatArg) -> TimedeltaType:
        """Multiply timedelta by a scalar."""
        return TimedeltaType(MulOp(self, factor))

    def __rmul__(self, factor: IntArg | FloatArg) -> TimedeltaType:
        return TimedeltaType(MulOp(factor, self))

    def __truediv__(self, divisor: IntArg | FloatArg | TimedeltaArg) -> TimedeltaType | FloatType:
        """Divide timedelta."""
        if isinstance(divisor, timedelta):
            divisor = TimedeltaType(divisor)
        if isinstance(divisor, TimedeltaType):
            return FloatType(DivOp(self, divisor))
        return TimedeltaType(DivOp(self, divisor))

    def __floordiv__(self, divisor: IntArg) -> TimedeltaType:
        """Floor divide timedelta by scalar."""
        return TimedeltaType(FloorDivOp(self, divisor))

    def __mod__(self, other: TimedeltaArg) -> TimedeltaType:
        """Modulo operation."""
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        return TimedeltaType(ModOp(self, other))
