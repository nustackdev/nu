"""Datetime Type."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING

from term.ops import AddOp, FuncCallOp, MethodCallOp, SubOp
from term.types import BaseType, ComparisonBase, FloatType, IntType, StrType
from term.typing import Sentinel

from every._abc import Arg, FloatArg, IntArg, StrArg
from everybase.type.timedelta import TimedeltaArg
from everybase.type.timezone import TimezoneType

from .args import DatetimeArg, TimezoneArg


if TYPE_CHECKING:
    from everybase.type.date import DateType
    from everybase.type.time import TimeType
    from everybase.type.timedelta import TimedeltaType

__all__ = [
    "DatetimeType",
]


class DatetimeType(
    ComparisonBase["datetime | DatetimeType"],
    BaseType[datetime | Sentinel],
):
    """Type representing a datetime.

    Supports comparison operations and datetime-specific methods.
    Stored as ISO format string for serialization.

    Example:
        >>> dt = DatetimeType.now()
        >>> dt.year()  # IntType
        >>> dt.timestamp()  # FloatType
        >>> dt.isoformat()  # StrType
        >>> dt > other_dt  # BoolType
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def now(cls, tz: TimezoneArg | None = None) -> DatetimeType:
        """Create a DatetimeType for the current time.

        Args:
            tz: Optional timezone. If None, uses local time.

        Returns:
            DatetimeType representing current time.
        """
        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneType(tz)
            return cls(FuncCallOp(datetime.now, tz))
        return cls(FuncCallOp(datetime.now))

    @classmethod
    def utcnow(cls) -> DatetimeType:
        """Create a DatetimeType for current UTC time."""
        return cls(FuncCallOp(datetime.now, TimezoneType(UTC)))

    @classmethod
    def from_timestamp(cls, ts: FloatArg, tz: TimezoneArg | None = None) -> DatetimeType:
        """Create a DatetimeType from a POSIX timestamp."""
        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneType(tz)
            return cls(FuncCallOp(datetime.fromtimestamp, ts, tz))
        return cls(FuncCallOp(datetime.fromtimestamp, ts))

    @classmethod
    def from_iso(cls, iso_str: StrArg) -> DatetimeType:
        """Create a DatetimeType from an ISO format string."""
        return cls(FuncCallOp(datetime.fromisoformat, iso_str))

    @classmethod
    def combine(
        cls,
        date: Arg[object],
        time: Arg[object],
        tzinfo: TimezoneArg | None = None,
    ) -> DatetimeType:
        """Combine a date and time into a datetime."""
        if tzinfo is not None:
            if isinstance(tzinfo, timezone):
                tzinfo = TimezoneType(tzinfo)
            return cls(FuncCallOp(datetime.combine, date, time, tzinfo))
        return cls(FuncCallOp(datetime.combine, date, time))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntType:
        """Get the year component."""
        return IntType(FuncCallOp(getattr, self, "year"))

    def month(self) -> IntType:
        """Get the month component (1-12)."""
        return IntType(FuncCallOp(getattr, self, "month"))

    def day(self) -> IntType:
        """Get the day component (1-31)."""
        return IntType(FuncCallOp(getattr, self, "day"))

    def hour(self) -> IntType:
        """Get the hour component (0-23)."""
        return IntType(FuncCallOp(getattr, self, "hour"))

    def minute(self) -> IntType:
        """Get the minute component (0-59)."""
        return IntType(FuncCallOp(getattr, self, "minute"))

    def second(self) -> IntType:
        """Get the second component (0-59)."""
        return IntType(FuncCallOp(getattr, self, "second"))

    def microsecond(self) -> IntType:
        """Get the microsecond component (0-999999)."""
        return IntType(FuncCallOp(getattr, self, "microsecond"))

    def weekday(self) -> IntType:
        """Get the day of week (Monday=0, Sunday=6)."""
        return IntType(MethodCallOp(self, "weekday"))

    def isoweekday(self) -> IntType:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        return IntType(MethodCallOp(self, "isoweekday"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def timestamp(self) -> FloatType:
        """Convert to POSIX timestamp."""
        return FloatType(MethodCallOp(self, "timestamp"))

    def isoformat(self, sep: StrArg = "T", timespec: StrArg = "auto") -> StrType:
        """Convert to ISO 8601 format string."""
        return StrType(MethodCallOp(self, "isoformat", sep, timespec))

    def date(self) -> DateType:
        """Extract the date component."""
        from everybase.type.date import DateType

        return DateType(MethodCallOp(self, "date"))

    def time(self) -> TimeType:
        """Extract the time component."""
        from everybase.type.time import TimeType

        return TimeType(MethodCallOp(self, "time"))

    def strftime(self, fmt: StrArg) -> StrType:
        """Format datetime as string."""
        return StrType(MethodCallOp(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: IntArg | None = None,
        month: IntArg | None = None,
        day: IntArg | None = None,
        hour: IntArg | None = None,
        minute: IntArg | None = None,
        second: IntArg | None = None,
        microsecond: IntArg | None = None,
    ) -> DatetimeType:
        """Create a new datetime with some components replaced."""
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
        return DatetimeType(MethodCallOp(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DatetimeType:
        """Add a timedelta to this datetime."""
        from datetime import timedelta

        from everybase.type.timedelta import TimedeltaType

        if isinstance(delta, timedelta):
            delta = TimedeltaType(delta)
        return DatetimeType(AddOp(self, delta))

    def __sub__(self, other: DatetimeArg | TimedeltaArg) -> DatetimeType | TimedeltaType:
        """Subtract a datetime or timedelta."""
        from datetime import timedelta

        from everybase.type.timedelta import TimedeltaType

        if isinstance(other, datetime):
            other = DatetimeType(other)
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        if isinstance(other, DatetimeType):
            return TimedeltaType(SubOp(self, other))
        return DatetimeType(SubOp(self, other))
