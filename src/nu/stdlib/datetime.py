"""Datetime types - timezone, timedelta, date, time, datetime.

All datetime types converted to the Interface/TypedNu pattern.
Each type has a private _*I(Form) mixin and a public *I leaf.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Arg, Form, Mode, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import BoolForm, FloatForm, IntForm, NoneForm, StrForm
    from nu.terms import Nu


__all__ = [
    "DateArg",
    "DateI",
    "DatetimeArg",
    "DatetimeI",
    "TimeArg",
    "TimeI",
    "TimedeltaArg",
    "TimedeltaI",
    "TimezoneArg",
    "TimezoneI",
]


# =============================================================================
# TYPE ALIASES
# =============================================================================

type DateArg = Arg[date]
type DatetimeArg = Arg[datetime]
type TimeArg = Arg[time]
type TimedeltaArg = Arg[timedelta]
type TimezoneArg = Arg[timezone]


# =============================================================================
# TIMEZONE
# =============================================================================


class _TimezoneI(Form):
    """Timezone operations mixin. Equalable only (no ordering)."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def utc(cls) -> TimezoneI:
        """Create a TimezoneI for UTC."""
        return TimezoneI(UTC)

    @classmethod
    def from_offset(
        cls,
        hours: int | Nu[int] = 0,
        minutes: int | Nu[int] = 0,
        name: str | Nu[str] | None = None,
    ) -> TimezoneI:
        """Create a TimezoneI from hour/minute offset."""
        from nu.terms import FuncCall

        offset = TimedeltaI.from_components(hours=hours, minutes=minutes)
        if name is not None:
            return TimezoneI(FuncCall(timezone, offset, name))
        return TimezoneI(FuncCall(timezone, offset))

    @classmethod
    def from_timedelta(
        cls,
        offset: TimedeltaArg,
        name: str | Nu[str] | None = None,
    ) -> TimezoneI:
        """Create a TimezoneI from a timedelta offset."""
        from nu.terms import FuncCall

        if isinstance(offset, timedelta):
            offset = TimedeltaI(offset)
        if name is not None:
            return TimezoneI(FuncCall(timezone, offset, name))
        return TimezoneI(FuncCall(timezone, offset))

    # =========================================================================
    # METHODS
    # =========================================================================

    def tzname(self, dt: DatetimeArg | None = None) -> StrForm:
        """Get the timezone name."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeI(dt)
        else:
            dt_arg = dt
        return StrForm(MethodCall(self, "tzname", dt_arg))

    def utcoffset(self, dt: DatetimeArg | None = None) -> TimedeltaI:
        """Get the UTC offset as timedelta."""
        from nu.terms import MethodCall

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeI(dt)
        else:
            dt_arg = dt
        return TimedeltaI(MethodCall(self, "utcoffset", dt_arg))

    def dst(self, dt: DatetimeArg | None = None) -> NoneForm:
        """Get the daylight saving time offset (returns None for fixed-offset timezones)."""
        from nu.forms.primitives import NoneForm

        return NoneForm()

    # =========================================================================
    # COMPARISON (equalable only - no ordering)
    # =========================================================================

    def eq(self, other: TimezoneArg) -> BoolForm:
        """Equality check."""
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: TimezoneArg) -> BoolForm:
        """Inequality check."""
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class TimezoneI(_TimezoneI, TypedNu[timezone]):
    """Timezone interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# TIMEDELTA
# =============================================================================


class _TimedeltaI(Form):
    """Timedelta operations mixin. Comparable + arithmetic."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_seconds(cls, seconds: float | Nu[float]) -> TimedeltaI:
        """Create a TimedeltaI from seconds."""
        from nu.terms import FuncCall

        return TimedeltaI(FuncCall(timedelta, seconds=seconds))

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
    ) -> TimedeltaI:
        """Create a TimedeltaI from time components."""
        from nu.terms import FuncCall

        return TimedeltaI(
            FuncCall(
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

    def days(self) -> IntForm:
        """Get the days component (normalized)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "days"))

    def seconds(self) -> IntForm:
        """Get the seconds component (0-86399)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "seconds"))

    def microseconds(self) -> IntForm:
        """Get the microseconds component (0-999999)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "microseconds"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def total_seconds(self) -> FloatForm:
        """Get total duration in seconds."""
        from nu.forms.primitives import FloatForm
        from nu.terms import MethodCall

        return FloatForm(MethodCall(self, "total_seconds"))

    def total_minutes(self) -> FloatForm:
        """Get total duration in minutes."""
        return self.total_seconds() / 60.0

    def total_hours(self) -> FloatForm:
        """Get total duration in hours."""
        return self.total_seconds() / 3600.0

    def total_days(self) -> FloatForm:
        """Get total duration in days."""
        return self.total_seconds() / 86400.0

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: TimedeltaArg) -> TimedeltaI:
        """Add two timedeltas."""
        from nu import Add

        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        return TimedeltaI(Add(self, other))

    def __radd__(self, other: timedelta) -> TimedeltaI:
        """Right add."""
        from nu import Add

        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        return TimedeltaI(Add(other, self))

    def __sub__(self, other: TimedeltaArg) -> TimedeltaI:
        """Subtract timedeltas."""
        from nu import Sub

        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        return TimedeltaI(Sub(self, other))

    def __rsub__(self, other: timedelta) -> TimedeltaI:
        """Right subtract."""
        from nu import Sub

        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        return TimedeltaI(Sub(other, self))

    def __mul__(self, factor: int | float | Nu) -> TimedeltaI:
        """Multiply timedelta by a scalar."""
        from nu import Mul

        return TimedeltaI(Mul(self, factor))

    def __rmul__(self, factor: int | float) -> TimedeltaI:
        """Right multiply."""
        from nu import Mul

        return TimedeltaI(Mul(factor, self))

    def __truediv__(self, divisor: int | float | TimedeltaArg) -> TimedeltaI | FloatForm:
        """Divide timedelta."""
        from nu import Div
        from nu.forms.primitives import FloatForm

        if isinstance(divisor, timedelta):
            divisor = TimedeltaI(divisor)
        if isinstance(divisor, _TimedeltaI):
            return FloatForm(Div(self, divisor))
        return TimedeltaI(Div(self, divisor))

    def __floordiv__(self, divisor: int | Nu[int]) -> TimedeltaI:
        """Floor divide timedelta by scalar."""
        from nu import FloorDiv

        return TimedeltaI(FloorDiv(self, divisor))

    def __mod__(self, other: TimedeltaArg) -> TimedeltaI:
        """Modulo operation."""
        from nu import Mod

        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        return TimedeltaI(Mod(self, other))

    def __neg__(self) -> TimedeltaI:
        """Negate."""
        from nu import Neg

        return TimedeltaI(Neg(self))

    def __abs__(self) -> TimedeltaI:
        """Absolute value."""
        from nu import Abs

        return TimedeltaI(Abs(self))

    def __pos__(self) -> TimedeltaI:
        """Unary positive (returns self)."""
        return self  # type: ignore[return-value]

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TimedeltaArg) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: TimedeltaArg) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: TimedeltaArg) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: TimedeltaArg) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: TimedeltaArg) -> BoolForm:
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: TimedeltaArg) -> BoolForm:
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class TimedeltaI(_TimedeltaI, TypedNu[timedelta]):
    """Timedelta interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# DATE
# =============================================================================


class _DateI(Form):
    """Date operations mixin. Comparable + date-specific methods."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def today(cls) -> DateI:
        """Create a DateI for today."""
        from nu.terms import FuncCall

        return DateI(FuncCall(date.today))

    @classmethod
    def from_iso(cls, iso_str: str | Nu[str]) -> DateI:
        """Create a DateI from an ISO format string (YYYY-MM-DD)."""
        from nu.terms import FuncCall, Sentinel

        def _safe_fromisoformat(s: object) -> date | Sentinel:
            if not isinstance(s, str):
                from nu import EMPTY

                return EMPTY
            return date.fromisoformat(s)

        return DateI(FuncCall(_safe_fromisoformat, iso_str))

    @classmethod
    def from_ordinal(cls, ordinal: int | Nu[int]) -> DateI:
        """Create a DateI from a Gregorian ordinal."""
        from nu.terms import FuncCall

        return DateI(FuncCall(date.fromordinal, ordinal))

    @classmethod
    def from_timestamp(cls, timestamp: float | Nu[float]) -> DateI:
        """Create a DateI from a POSIX timestamp."""
        from nu.terms import FuncCall

        return DateI(FuncCall(date.fromtimestamp, timestamp))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntForm:
        """Get the year component."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "year"))

    def month(self) -> IntForm:
        """Get the month component (1-12)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "month"))

    def day(self) -> IntForm:
        """Get the day component (1-31)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "day"))

    def weekday(self) -> IntForm:
        """Get the day of week (Monday=0, Sunday=6)."""
        from nu.forms.primitives import IntForm
        from nu.terms import MethodCall

        return IntForm(MethodCall(self, "weekday"))

    def isoweekday(self) -> IntForm:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        from nu.forms.primitives import IntForm
        from nu.terms import MethodCall

        return IntForm(MethodCall(self, "isoweekday"))

    def toordinal(self) -> IntForm:
        """Get the Gregorian ordinal."""
        from nu.forms.primitives import IntForm
        from nu.terms import MethodCall

        return IntForm(MethodCall(self, "toordinal"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self) -> StrForm:
        """Convert to ISO 8601 format string (YYYY-MM-DD)."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "isoformat"))

    def strftime(self, fmt: str | Nu[str]) -> StrForm:
        """Format date as string."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "strftime", fmt))

    def ctime(self) -> StrForm:
        """Return ctime-style string."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "ctime"))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: int | Nu[int] | None = None,
        month: int | Nu[int] | None = None,
        day: int | Nu[int] | None = None,
    ) -> DateI:
        """Create a new date with some components replaced."""
        from nu.terms import MethodCall

        kwargs = {}
        if year is not None:
            kwargs["year"] = year
        if month is not None:
            kwargs["month"] = month
        if day is not None:
            kwargs["day"] = day
        return DateI(MethodCall(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DateI:
        """Add a timedelta to this date."""
        from nu import Add

        if isinstance(delta, timedelta):
            delta = TimedeltaI(delta)
        return DateI(Add(self, delta))

    def __sub__(self, other: DateArg | TimedeltaArg) -> DateI | TimedeltaI:
        """Subtract a date or timedelta."""
        from nu import Sub

        if isinstance(other, date):
            other = DateI(other)
        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        if isinstance(other, _DateI):
            return TimedeltaI(Sub(self, other))
        return DateI(Sub(self, other))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DateArg) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: DateArg) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: DateArg) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: DateArg) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: DateArg) -> BoolForm:
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: DateArg) -> BoolForm:
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class DateI(_DateI, TypedNu[date]):
    """Date interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# TIME
# =============================================================================


class _TimeI(Form):
    """Time operations mixin. Comparable + time-specific methods."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_iso(cls, iso_str: str | Nu[str]) -> TimeI:
        """Create a TimeI from an ISO format string (HH:MM:SS[.ffffff])."""
        from nu.terms import FuncCall, Sentinel

        def _safe_fromisoformat(s: object) -> time | Sentinel:
            if not isinstance(s, str):
                from nu import EMPTY

                return EMPTY
            return time.fromisoformat(s)

        return TimeI(FuncCall(_safe_fromisoformat, iso_str))

    @classmethod
    def from_components(
        cls,
        hour: int | Nu[int] = 0,
        minute: int | Nu[int] = 0,
        second: int | Nu[int] = 0,
        microsecond: int | Nu[int] = 0,
    ) -> TimeI:
        """Create a TimeI from time components."""
        from nu.terms import FuncCall

        return TimeI(FuncCall(time, hour, minute, second, microsecond))

    @classmethod
    def midnight(cls) -> TimeI:
        """Create a TimeI for midnight (00:00:00)."""
        return cls.from_components(0, 0, 0)

    @classmethod
    def noon(cls) -> TimeI:
        """Create a TimeI for noon (12:00:00)."""
        return cls.from_components(12, 0, 0)

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def hour(self) -> IntForm:
        """Get the hour component (0-23)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "hour"))

    def minute(self) -> IntForm:
        """Get the minute component (0-59)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "minute"))

    def second(self) -> IntForm:
        """Get the second component (0-59)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "second"))

    def microsecond(self) -> IntForm:
        """Get the microsecond component (0-999999)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "microsecond"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self, timespec: str | Nu[str] = "auto") -> StrForm:
        """Convert to ISO 8601 format string."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "isoformat", timespec))

    def strftime(self, fmt: str | Nu[str]) -> StrForm:
        """Format time as string."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        hour: int | Nu[int] | None = None,
        minute: int | Nu[int] | None = None,
        second: int | Nu[int] | None = None,
        microsecond: int | Nu[int] | None = None,
    ) -> TimeI:
        """Create a new time with some components replaced."""
        from nu.terms import MethodCall

        kwargs = {}
        if hour is not None:
            kwargs["hour"] = hour
        if minute is not None:
            kwargs["minute"] = minute
        if second is not None:
            kwargs["second"] = second
        if microsecond is not None:
            kwargs["microsecond"] = microsecond
        return TimeI(MethodCall(self, "replace", **kwargs))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TimeArg) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: TimeArg) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: TimeArg) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: TimeArg) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: TimeArg) -> BoolForm:
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: TimeArg) -> BoolForm:
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class TimeI(_TimeI, TypedNu[time]):
    """Time interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# DATETIME
# =============================================================================


class _DatetimeI(Form):
    """Datetime operations mixin. Comparable + datetime-specific methods."""

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def now(cls, tz: TimezoneArg | None = None) -> DatetimeI:
        """Create a DatetimeI for the current time."""
        from nu.terms import FuncCall

        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneI(tz)
            return DatetimeI(FuncCall(datetime.now, tz))
        return DatetimeI(FuncCall(datetime.now))

    @classmethod
    def utcnow(cls) -> DatetimeI:
        """Create a DatetimeI for current UTC time."""
        from nu.terms import FuncCall

        return DatetimeI(FuncCall(datetime.now, TimezoneI(UTC)))

    @classmethod
    def from_timestamp(cls, ts: float | Nu[float], tz: TimezoneArg | None = None) -> DatetimeI:
        """Create a DatetimeI from a POSIX timestamp."""
        from nu.terms import FuncCall

        if tz is not None:
            if isinstance(tz, timezone):
                tz = TimezoneI(tz)
            return DatetimeI(FuncCall(datetime.fromtimestamp, ts, tz))
        return DatetimeI(FuncCall(datetime.fromtimestamp, ts))

    @classmethod
    def from_iso(cls, iso_str: str | Nu[str]) -> DatetimeI:
        """Create a DatetimeI from an ISO format string."""
        from nu.terms import FuncCall, Sentinel

        def _safe_fromisoformat(s: object) -> datetime | Sentinel:
            if not isinstance(s, str):
                from nu import EMPTY

                return EMPTY
            return datetime.fromisoformat(s)

        return DatetimeI(FuncCall(_safe_fromisoformat, iso_str))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntForm:
        """Get the year component."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "year"))

    def month(self) -> IntForm:
        """Get the month component (1-12)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "month"))

    def day(self) -> IntForm:
        """Get the day component (1-31)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "day"))

    def hour(self) -> IntForm:
        """Get the hour component (0-23)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "hour"))

    def minute(self) -> IntForm:
        """Get the minute component (0-59)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "minute"))

    def second(self) -> IntForm:
        """Get the second component (0-59)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "second"))

    def microsecond(self) -> IntForm:
        """Get the microsecond component (0-999999)."""
        from nu.forms.primitives import IntForm
        from nu.terms import FuncCall

        return IntForm(FuncCall(getattr, self, "microsecond"))

    def weekday(self) -> IntForm:
        """Get the day of week (Monday=0, Sunday=6)."""
        from nu.forms.primitives import IntForm
        from nu.terms import MethodCall

        return IntForm(MethodCall(self, "weekday"))

    def isoweekday(self) -> IntForm:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        from nu.forms.primitives import IntForm
        from nu.terms import MethodCall

        return IntForm(MethodCall(self, "isoweekday"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def timestamp(self) -> FloatForm:
        """Convert to POSIX timestamp."""
        from nu.forms.primitives import FloatForm
        from nu.terms import MethodCall

        return FloatForm(MethodCall(self, "timestamp"))

    def isoformat(self, sep: str | Nu[str] = "T", timespec: str | Nu[str] = "auto") -> StrForm:
        """Convert to ISO 8601 format string."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "isoformat", sep, timespec))

    def date(self) -> DateI:
        """Extract the date component."""
        from nu.terms import MethodCall

        return DateI(MethodCall(self, "date"))

    def time(self) -> TimeI:
        """Extract the time component."""
        from nu.terms import MethodCall

        return TimeI(MethodCall(self, "time"))

    def strftime(self, fmt: str | Nu[str]) -> StrForm:
        """Format datetime as string."""
        from nu.forms.primitives import StrForm
        from nu.terms import MethodCall

        return StrForm(MethodCall(self, "strftime", fmt))

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
    ) -> DatetimeI:
        """Create a new datetime with some components replaced."""
        from nu.terms import MethodCall

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
        return DatetimeI(MethodCall(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DatetimeI:
        """Add a timedelta to this datetime."""
        from nu import Add

        if isinstance(delta, timedelta):
            delta = TimedeltaI(delta)
        return DatetimeI(Add(self, delta))

    def __sub__(self, other: DatetimeArg | TimedeltaArg) -> DatetimeI | TimedeltaI:
        """Subtract a datetime or timedelta."""
        from nu import Sub

        if isinstance(other, datetime):
            other = DatetimeI(other)
        if isinstance(other, timedelta):
            other = TimedeltaI(other)
        if isinstance(other, _DatetimeI):
            return TimedeltaI(Sub(self, other))
        return DatetimeI(Sub(self, other))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DatetimeArg) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: DatetimeArg) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: DatetimeArg) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: DatetimeArg) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: DatetimeArg) -> BoolForm:
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: DatetimeArg) -> BoolForm:
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))


class DatetimeI(_DatetimeI, TypedNu[datetime]):
    """Datetime interface."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
    pass
