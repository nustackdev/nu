"""Datetime ref base for datetime values.

DatetimeRefBase = RefBase[datetime] + Comparable + datetime operations.
Stored as ISO format string.
"""

from __future__ import annotations

from abc import ABC
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from every import Term
    from everybase.py import FloatRef, IntRef, StrRef

    from .args import DatetimeArg, TimedeltaArg, TimezoneArg
    from .py.refs import DateRef, DatetimeRef, TimedeltaRef, TimeRef


__all__ = [
    "DatetimeRefBase",
]


class DatetimeRefBase(
    Comparable["datetime | DatetimeRef"],
    RefBase[datetime],
    ABC,
):
    """Abstract base for datetime refs.

    Supports comparison operations and datetime-specific methods.
    Stored as ISO format string for serialization.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def now(cls, tz: TimezoneArg | None = None) -> DatetimeRef:
        """Create a DatetimeRef for the current time."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DatetimeRef, TimezoneRef

        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneRef(tz)
            return DatetimeRef(FuncCallOp(datetime.now, tz))
        return DatetimeRef(FuncCallOp(datetime.now))

    @classmethod
    def utcnow(cls) -> DatetimeRef:
        """Create a DatetimeRef for current UTC time."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DatetimeRef, TimezoneRef

        return DatetimeRef(FuncCallOp(datetime.now, TimezoneRef(UTC)))

    @classmethod
    def from_timestamp(cls, ts: float | Term[float], tz: TimezoneArg | None = None) -> DatetimeRef:
        """Create a DatetimeRef from a POSIX timestamp."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DatetimeRef, TimezoneRef

        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneRef(tz)
            return DatetimeRef(FuncCallOp(datetime.fromtimestamp, ts, tz))
        return DatetimeRef(FuncCallOp(datetime.fromtimestamp, ts))

    @classmethod
    def from_iso(cls, iso_str: str | Term[str]) -> DatetimeRef:
        """Create a DatetimeRef from an ISO format string."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DatetimeRef

        return DatetimeRef(FuncCallOp(datetime.fromisoformat, iso_str))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntRef:
        """Get the year component."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "year"))

    def month(self) -> IntRef:
        """Get the month component (1-12)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "month"))

    def day(self) -> IntRef:
        """Get the day component (1-31)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "day"))

    def hour(self) -> IntRef:
        """Get the hour component (0-23)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "hour"))

    def minute(self) -> IntRef:
        """Get the minute component (0-59)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "minute"))

    def second(self) -> IntRef:
        """Get the second component (0-59)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "second"))

    def microsecond(self) -> IntRef:
        """Get the microsecond component (0-999999)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "microsecond"))

    def weekday(self) -> IntRef:
        """Get the day of week (Monday=0, Sunday=6)."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "weekday"))

    def isoweekday(self) -> IntRef:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "isoweekday"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def timestamp(self) -> FloatRef:
        """Convert to POSIX timestamp."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import FloatRef

        return FloatRef(MethodCallOp(self, "timestamp"))

    def isoformat(self, sep: str | Term[str] = "T", timespec: str | Term[str] = "auto") -> StrRef:
        """Convert to ISO 8601 format string."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "isoformat", sep, timespec))

    def date(self) -> DateRef:
        """Extract the date component."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DateRef

        return DateRef(MethodCallOp(self, "date"))

    def time(self) -> TimeRef:
        """Extract the time component."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import TimeRef

        return TimeRef(MethodCallOp(self, "time"))

    def strftime(self, fmt: str | Term[str]) -> StrRef:
        """Format datetime as string."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: int | Term[int] | None = None,
        month: int | Term[int] | None = None,
        day: int | Term[int] | None = None,
        hour: int | Term[int] | None = None,
        minute: int | Term[int] | None = None,
        second: int | Term[int] | None = None,
        microsecond: int | Term[int] | None = None,
    ) -> DatetimeRef:
        """Create a new datetime with some components replaced."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DatetimeRef

        kwargs = {}
        if year is not None:
            kwargs["year"] = year
        if month is not None:
            kwargs["month"] = month
        if day is not None:
            kwargs["day"] = day
        if hour is not None:
            kwargs["hour"] = hour
        if minute is not None:
            kwargs["minute"] = minute
        if second is not None:
            kwargs["second"] = second
        if microsecond is not None:
            kwargs["microsecond"] = microsecond
        return DatetimeRef(MethodCallOp(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DatetimeRef:
        """Add a timedelta to this datetime."""
        from datetime import timedelta

        from everybase.morphisms import AddOp

        from .py.refs import DatetimeRef, TimedeltaRef

        if isinstance(delta, timedelta):
            delta = TimedeltaRef(delta)
        return DatetimeRef(AddOp(self, delta))

    def __sub__(self, other: DatetimeArg | TimedeltaArg) -> DatetimeRef | TimedeltaRef:
        """Subtract a datetime or timedelta."""
        from datetime import timedelta

        from everybase.morphisms import SubOp

        from .py.refs import DatetimeRef, TimedeltaRef

        if isinstance(other, datetime):
            other = DatetimeRef(other)
        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        if isinstance(other, DatetimeRef):
            return TimedeltaRef(SubOp(self, other))
        return DatetimeRef(SubOp(self, other))
