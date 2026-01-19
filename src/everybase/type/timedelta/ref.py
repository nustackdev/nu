"""Timedelta Ref."""

from __future__ import annotations

from datetime import timedelta

from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef
from everyterm.ops import MethodCallOp
from everyterm.types import FloatType, IntType

from .args import TimedeltaArg
from .type import TimedeltaType


__all__ = [
    "TimedeltaRef",
]


class TimedeltaRef(CollectionItemRefBase[timedelta, TimedeltaType], PrimitiveRef):
    """Reference to a timedelta value in storage."""

    def set(self, value: TimedeltaArg) -> TimedeltaType:
        """Set the timedelta value."""
        if isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = MethodCallOp(value, "total_seconds")
        return TimedeltaType(TypedSetCmd(self, val))

    def get(self) -> TimedeltaType:
        """Get the timedelta value."""
        return TimedeltaType.from_seconds(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def days(self) -> IntType:
        return self.get().days()

    def seconds(self) -> IntType:
        return self.get().seconds()

    def microseconds(self) -> IntType:
        return self.get().microseconds()

    def total_seconds(self) -> FloatType:
        return self.get().total_seconds()

    def total_minutes(self) -> FloatType:
        return self.get().total_minutes()

    def total_hours(self) -> FloatType:
        return self.get().total_hours()

    def total_days(self) -> FloatType:
        return self.get().total_days()
