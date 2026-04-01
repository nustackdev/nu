"""Datetime type for datetime values.

Pattern:
    DatetimeType = Object[datetime] + ComparableBase + datetime operations
    DatetimeValue = ValueBase + DatetimeType (computed results)
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    ComparableBase,
    FloatValue,
    IntValue,
    Object,
    StrValue,
    ValueBase,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import DatetimeArg, TimedeltaArg, TimezoneArg


__all__ = [
    "DatetimeType",
    "DatetimeValue",
]


class DatetimeType(
    ComparableBase["datetime | DatetimeType"],
    Object[datetime | Sentinel],
):
    """Abstract type for datetime operations.

    Supports comparison operations and datetime-specific methods.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def now(cls, tz: TimezoneArg | None = None) -> DatetimeValue:
        """Create a DatetimeValue for the current time."""
        from nu import FuncCallOp

        from .timezone_ref import TimezoneValue

        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneValue(tz)
            return DatetimeValue(FuncCallOp(datetime.now, tz))
        return DatetimeValue(FuncCallOp(datetime.now))

    @classmethod
    def utcnow(cls) -> DatetimeValue:
        """Create a DatetimeValue for current UTC time."""
        from nu import FuncCallOp

        from .timezone_ref import TimezoneValue

        return DatetimeValue(FuncCallOp(datetime.now, TimezoneValue(UTC)))

    @classmethod
    def from_timestamp(
        cls, ts: float | Nu[float], tz: TimezoneArg | None = None
    ) -> DatetimeValue:
        """Create a DatetimeValue from a POSIX timestamp."""
        from nu import FuncCallOp

        from .timezone_ref import TimezoneValue

        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneValue(tz)
            return DatetimeValue(FuncCallOp(datetime.fromtimestamp, ts, tz))
        return DatetimeValue(FuncCallOp(datetime.fromtimestamp, ts))

    @classmethod
    def from_iso(cls, iso_str: str | Nu[str]) -> DatetimeValue:
        """Create a DatetimeValue from an ISO format string."""
        from nu import FuncCallOp

        def _safe_fromisoformat(s: object) -> datetime | Sentinel:
            if not isinstance(s, str):
                from nu import EMPTY

                return EMPTY
            return datetime.fromisoformat(s)

        return DatetimeValue(FuncCallOp(_safe_fromisoformat, iso_str))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntValue:
        """Get the year component."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "year"))

    def month(self) -> IntValue:
        """Get the month component (1-12)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "month"))

    def day(self) -> IntValue:
        """Get the day component (1-31)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "day"))

    def hour(self) -> IntValue:
        """Get the hour component (0-23)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "hour"))

    def minute(self) -> IntValue:
        """Get the minute component (0-59)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "minute"))

    def second(self) -> IntValue:
        """Get the second component (0-59)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "second"))

    def microsecond(self) -> IntValue:
        """Get the microsecond component (0-999999)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "microsecond"))

    def weekday(self) -> IntValue:
        """Get the day of week (Monday=0, Sunday=6)."""
        from nu import MethodCallOp

        return IntValue(MethodCallOp(self, "weekday"))

    def isoweekday(self) -> IntValue:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        from nu import MethodCallOp

        return IntValue(MethodCallOp(self, "isoweekday"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def timestamp(self) -> FloatValue:
        """Convert to POSIX timestamp."""
        from nu import MethodCallOp

        return FloatValue(MethodCallOp(self, "timestamp"))

    def isoformat(self, sep: str | Nu[str] = "T", timespec: str | Nu[str] = "auto") -> StrValue:
        """Convert to ISO 8601 format string."""
        from nu import MethodCallOp

        return StrValue(MethodCallOp(self, "isoformat", sep, timespec))

    def date(self) -> DateValue:
        """Extract the date component."""
        from nu import MethodCallOp

        from .date_ref import DateValue

        return DateValue(MethodCallOp(self, "date"))

    def time(self) -> TimeValue:
        """Extract the time component."""
        from nu import MethodCallOp

        from .time_ref import TimeValue

        return TimeValue(MethodCallOp(self, "time"))

    def strftime(self, fmt: str | Nu[str]) -> StrValue:
        """Format datetime as string."""
        from nu import MethodCallOp

        return StrValue(MethodCallOp(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: int | Nu[int] | None = None,
        month: int | Nu[int] | None = None,
        day: int | Nu[int] | None = None,
        hour: int | Nu[int] | None = None,
        minute: int | Nu[int] | None = None,
        second: int | Nu[int] | None = None,
        microsecond: int | Nu[int] | None = None,
    ) -> DatetimeValue:
        """Create a new datetime with some components replaced."""
        from nu import MethodCallOp

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
        return DatetimeValue(MethodCallOp(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DatetimeValue:
        """Add a timedelta to this datetime."""
        from datetime import timedelta

        from nu import AddOp

        from .timedelta_ref import TimedeltaValue

        if isinstance(delta, timedelta):
            delta = TimedeltaValue(delta)
        return DatetimeValue(AddOp(self, delta))

    def __sub__(self, other: DatetimeArg | TimedeltaArg) -> DatetimeValue | TimedeltaValue:
        """Subtract a datetime or timedelta."""
        from datetime import timedelta

        from nu import SubOp

        from .timedelta_ref import TimedeltaValue

        if isinstance(other, datetime):
            other = DatetimeValue(other)
        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        if isinstance(other, DatetimeType):
            return TimedeltaValue(SubOp(self, other))
        return DatetimeValue(SubOp(self, other))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class DatetimeValue(ValueBase, DatetimeType):
    """Computed datetime value (Python memory substrate)."""

    pass


# Forward references for type hints
if TYPE_CHECKING:
    from .date_ref import DateValue
    from .time_ref import TimeValue
    from .timedelta_ref import TimedeltaValue
