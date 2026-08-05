"""The ``datetime`` classes as Forms: timedelta, time, date, datetime, timezone.

Class names are lowercase to mirror ``from datetime import date, timedelta``
(hence ``# noqa: N801``). Each is the typed access surface for its stdlib type:

- **property reads** (``.year``, ``.hour``, ``.days`` ...) reuse core ``GetAttr``.
- **method calls** (``weekday()``, ``isoformat()``, ``total_seconds()``,
  ``replace(...)`` ...) are named ``ScalarQueryFactory`` atoms in ``interactions``
  (each binds the unbound method).
- **arithmetic** (``date + timedelta``, ``timedelta * n`` ...) reuses the core
  arithmetic atoms - Python performs the real op on the resolved values.
- **comparison** reuses the core comparison atoms.
- **constructors** are ``ScalarQueryFactory`` atoms in ``interactions``; the
  literal constructor is ``.of(...)`` since ``__init__`` wraps a Nu term.

Classes are ordered so each is defined before another references it.

Deferred (same pattern, fill in later): ``strptime``, ``isocalendar``,
``fromisocalendar``, ``astimezone``, ``utcnow`` (deprecated), ``fold``.
"""

from __future__ import annotations

from datetime import date as _date
from datetime import datetime as _datetime
from datetime import time as _time
from datetime import timedelta as _timedelta
from datetime import timezone as _timezone
from typing import TYPE_CHECKING, overload

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.forms.primitives import Bool, Float, Int, None_, Str
    from nu.lang import Arg, FloatArg, IntArg, StrArg

    type DateArg = Arg[_date]
    type DatetimeArg = Arg[_datetime]
    type TimeArg = Arg[_time]
    type TimedeltaArg = Arg[_timedelta]
    type TimezoneArg = Arg[_timezone]


__all__ = ["date", "datetime", "time", "timedelta", "timezone"]


class timedelta(Form, TypedNu[_timedelta]):  # noqa: N801
    """``datetime.timedelta`` as a Form - a span of time."""

    @classmethod
    def of(
        cls,
        *,
        days: IntArg | FloatArg = 0,
        seconds: IntArg | FloatArg = 0,
        microseconds: IntArg | FloatArg = 0,
        milliseconds: IntArg | FloatArg = 0,
        minutes: IntArg | FloatArg = 0,
        hours: IntArg | FloatArg = 0,
        weeks: IntArg | FloatArg = 0,
    ) -> timedelta:
        """Build a timedelta from its components: ``timedelta(...)``."""
        from .interactions import TimedeltaOf

        # positional in the stdlib timedelta() order
        return timedelta(
            TimedeltaOf(days, seconds, microseconds, milliseconds, minutes, hours, weeks)
        )

    def days(self) -> Int:
        """The whole-days component."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "days"))

    def seconds(self) -> Int:
        """The seconds component (0..86399)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "seconds"))

    def microseconds(self) -> Int:
        """The microseconds component (0..999999)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "microseconds"))

    def total_seconds(self) -> Float:
        """The total duration in seconds."""
        from nu.forms import Float

        from .interactions import TimedeltaTotalSeconds

        return Float(TimedeltaTotalSeconds(self))

    def __add__(self, other: TimedeltaArg) -> timedelta:
        from nu.core import Add

        return timedelta(Add(self, other))

    def __sub__(self, other: TimedeltaArg) -> timedelta:
        from nu.core import Sub

        return timedelta(Sub(self, other))

    def __mul__(self, factor: IntArg | FloatArg) -> timedelta:
        from nu.core import Mul

        return timedelta(Mul(self, factor))

    @overload
    def __truediv__(self, other: timedelta | _timedelta) -> Float: ...
    @overload
    def __truediv__(self, other: IntArg | FloatArg) -> timedelta: ...
    def __truediv__(self, other: TimedeltaArg | IntArg | FloatArg) -> timedelta | Float:
        from nu.core import Div

        if isinstance(other, (timedelta, _timedelta)):
            from nu.forms import Float

            return Float(Div(self, other))
        return timedelta(Div(self, other))

    def __floordiv__(self, other: IntArg) -> timedelta:
        from nu.core import FloorDiv

        return timedelta(FloorDiv(self, other))

    def __mod__(self, other: TimedeltaArg) -> timedelta:
        from nu.core import Mod

        return timedelta(Mod(self, other))

    def __neg__(self) -> timedelta:
        from nu.core import Neg

        return timedelta(Neg(self))

    def __abs__(self) -> timedelta:
        from nu.core import Abs

        return timedelta(Abs(self))

    def __pos__(self) -> timedelta:
        from nu.core import Pos

        return timedelta(Pos(self))

    def __gt__(self, other: TimedeltaArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: TimedeltaArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: TimedeltaArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: TimedeltaArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: TimedeltaArg) -> Bool:
        """Whether two spans are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: TimedeltaArg) -> Bool:
        """Whether two spans differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))


class time(Form, TypedNu[_time]):  # noqa: N801
    """``datetime.time`` as a Form - a wall-clock time of day."""

    @classmethod
    def of(
        cls,
        hour: IntArg = 0,
        minute: IntArg = 0,
        second: IntArg = 0,
        microsecond: IntArg = 0,
    ) -> time:
        """Build a time: ``time(hour, minute, second, microsecond)``."""
        from .interactions import TimeOf

        return time(TimeOf(hour, minute, second, microsecond))

    @classmethod
    def from_iso(cls, value: StrArg) -> time:
        """Parse an ISO time string: ``time.fromisoformat(s)``."""
        from .interactions import TimeFromIso

        return time(TimeFromIso(value))

    def hour(self) -> Int:
        """The hour (0..23)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "hour"))

    def minute(self) -> Int:
        """The minute (0..59)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "minute"))

    def second(self) -> Int:
        """The second (0..59)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "second"))

    def microsecond(self) -> Int:
        """The microsecond (0..999999)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "microsecond"))

    def isoformat(self) -> Str:
        """The time as an ISO string."""
        from nu.forms import Str

        from .interactions import TimeIsoformat

        return Str(TimeIsoformat(self))

    def strftime(self, fmt: StrArg) -> Str:
        """Format the time with a strftime pattern."""
        from nu.forms import Str

        from .interactions import TimeStrftime

        return Str(TimeStrftime(self, fmt))

    def replace(
        self,
        *,
        hour: IntArg | None = None,
        minute: IntArg | None = None,
        second: IntArg | None = None,
        microsecond: IntArg | None = None,
    ) -> time:
        """A copy with the given components replaced."""
        from .interactions import TimeReplace

        kw: dict[str, object] = {}
        if hour is not None:
            kw["hour"] = hour
        if minute is not None:
            kw["minute"] = minute
        if second is not None:
            kw["second"] = second
        if microsecond is not None:
            kw["microsecond"] = microsecond
        return time(TimeReplace(self, **kw))

    def __gt__(self, other: TimeArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: TimeArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: TimeArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: TimeArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: TimeArg) -> Bool:
        """Whether two times are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: TimeArg) -> Bool:
        """Whether two times differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))


class date(Form, TypedNu[_date]):  # noqa: N801
    """``datetime.date`` as a Form - a calendar date."""

    @classmethod
    def of(cls, year: IntArg, month: IntArg, day: IntArg) -> date:
        """Build a date: ``date(year, month, day)``."""
        from .interactions import DateOf

        return date(DateOf(year, month, day))

    @classmethod
    def today(cls) -> date:
        """Today's date: ``date.today()``."""
        from .interactions import DateToday

        return date(DateToday())

    @classmethod
    def from_iso(cls, value: StrArg) -> date:
        """Parse an ISO date string: ``date.fromisoformat(s)``."""
        from .interactions import DateFromIso

        return date(DateFromIso(value))

    @classmethod
    def from_ordinal(cls, value: IntArg) -> date:
        """From a proleptic Gregorian ordinal: ``date.fromordinal(n)``."""
        from .interactions import DateFromOrdinal

        return date(DateFromOrdinal(value))

    @classmethod
    def from_timestamp(cls, value: FloatArg) -> date:
        """From a POSIX timestamp: ``date.fromtimestamp(t)``."""
        from .interactions import DateFromTimestamp

        return date(DateFromTimestamp(value))

    def year(self) -> Int:
        """The year."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "year"))

    def month(self) -> Int:
        """The month (1..12)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "month"))

    def day(self) -> Int:
        """The day of the month (1..31)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "day"))

    def weekday(self) -> Int:
        """The day of week, Monday=0."""
        from nu.forms import Int

        from .interactions import DateWeekday

        return Int(DateWeekday(self))

    def isoweekday(self) -> Int:
        """The day of week, Monday=1."""
        from nu.forms import Int

        from .interactions import DateIsoweekday

        return Int(DateIsoweekday(self))

    def toordinal(self) -> Int:
        """The proleptic Gregorian ordinal."""
        from nu.forms import Int

        from .interactions import DateToordinal

        return Int(DateToordinal(self))

    def isoformat(self) -> Str:
        """The date as an ISO string (YYYY-MM-DD)."""
        from nu.forms import Str

        from .interactions import DateIsoformat

        return Str(DateIsoformat(self))

    def ctime(self) -> Str:
        """The date as a C-style string."""
        from nu.forms import Str

        from .interactions import DateCtime

        return Str(DateCtime(self))

    def strftime(self, fmt: StrArg) -> Str:
        """Format the date with a strftime pattern."""
        from nu.forms import Str

        from .interactions import DateStrftime

        return Str(DateStrftime(self, fmt))

    def replace(
        self,
        *,
        year: IntArg | None = None,
        month: IntArg | None = None,
        day: IntArg | None = None,
    ) -> date:
        """A copy with the given components replaced."""
        from .interactions import DateReplace

        kw: dict[str, object] = {}
        if year is not None:
            kw["year"] = year
        if month is not None:
            kw["month"] = month
        if day is not None:
            kw["day"] = day
        return date(DateReplace(self, **kw))

    def __add__(self, other: TimedeltaArg) -> date:
        from nu.core import Add

        return date(Add(self, other))

    @overload
    def __sub__(self, other: date | _date) -> timedelta: ...
    @overload
    def __sub__(self, other: timedelta | _timedelta) -> date: ...
    def __sub__(self, other: DateArg | TimedeltaArg) -> date | timedelta:
        from nu.core import Sub

        if isinstance(other, (date, _date)):
            return timedelta(Sub(self, other))
        return date(Sub(self, other))

    def __gt__(self, other: DateArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: DateArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: DateArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: DateArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: DateArg) -> Bool:
        """Whether two dates are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: DateArg) -> Bool:
        """Whether two dates differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))


class datetime(Form, TypedNu[_datetime]):  # noqa: N801
    """``datetime.datetime`` as a Form - a date and a time."""

    @classmethod
    def of(
        cls,
        year: IntArg,
        month: IntArg,
        day: IntArg,
        hour: IntArg = 0,
        minute: IntArg = 0,
        second: IntArg = 0,
        microsecond: IntArg = 0,
    ) -> datetime:
        """Build a datetime: ``datetime(year, month, day, hour, ...)``."""
        from .interactions import DatetimeOf

        return datetime(DatetimeOf(year, month, day, hour, minute, second, microsecond))

    @classmethod
    def now(cls, tz: TimezoneArg | None = None) -> datetime:
        """The current local (or ``tz``) datetime: ``datetime.now(tz)``."""
        from .interactions import DatetimeNow

        if tz is not None:
            return datetime(DatetimeNow(tz))
        return datetime(DatetimeNow())

    @classmethod
    def from_iso(cls, value: StrArg) -> datetime:
        """Parse an ISO datetime string: ``datetime.fromisoformat(s)``."""
        from .interactions import DatetimeFromIso

        return datetime(DatetimeFromIso(value))

    @classmethod
    def from_timestamp(cls, value: FloatArg, tz: TimezoneArg | None = None) -> datetime:
        """From a POSIX timestamp: ``datetime.fromtimestamp(ts, tz)``."""
        from .interactions import DatetimeFromTimestamp

        if tz is not None:
            return datetime(DatetimeFromTimestamp(value, tz))
        return datetime(DatetimeFromTimestamp(value))

    @classmethod
    def combine(cls, date_value: DateArg, time_value: TimeArg) -> datetime:
        """Combine a date and a time: ``datetime.combine(date, time)``."""
        from .interactions import DatetimeCombine

        return datetime(DatetimeCombine(date_value, time_value))

    def year(self) -> Int:
        """The year."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "year"))

    def month(self) -> Int:
        """The month (1..12)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "month"))

    def day(self) -> Int:
        """The day of the month (1..31)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "day"))

    def hour(self) -> Int:
        """The hour (0..23)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "hour"))

    def minute(self) -> Int:
        """The minute (0..59)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "minute"))

    def second(self) -> Int:
        """The second (0..59)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "second"))

    def microsecond(self) -> Int:
        """The microsecond (0..999999)."""
        from nu.core import GetAttr
        from nu.forms import Int

        return Int(GetAttr(self, "microsecond"))

    def weekday(self) -> Int:
        """The day of week, Monday=0."""
        from nu.forms import Int

        from .interactions import DatetimeWeekday

        return Int(DatetimeWeekday(self))

    def isoweekday(self) -> Int:
        """The day of week, Monday=1."""
        from nu.forms import Int

        from .interactions import DatetimeIsoweekday

        return Int(DatetimeIsoweekday(self))

    def timestamp(self) -> Float:
        """The POSIX timestamp."""
        from nu.forms import Float

        from .interactions import DatetimeTimestamp

        return Float(DatetimeTimestamp(self))

    def isoformat(self) -> Str:
        """The datetime as an ISO string."""
        from nu.forms import Str

        from .interactions import DatetimeIsoformat

        return Str(DatetimeIsoformat(self))

    def strftime(self, fmt: StrArg) -> Str:
        """Format the datetime with a strftime pattern."""
        from nu.forms import Str

        from .interactions import DatetimeStrftime

        return Str(DatetimeStrftime(self, fmt))

    def date(self) -> date:
        """The date part."""
        from .interactions import DatetimeDate

        return date(DatetimeDate(self))

    def time(self) -> time:
        """The time part."""
        from .interactions import DatetimeTime

        return time(DatetimeTime(self))

    def replace(
        self,
        *,
        year: IntArg | None = None,
        month: IntArg | None = None,
        day: IntArg | None = None,
        hour: IntArg | None = None,
        minute: IntArg | None = None,
        second: IntArg | None = None,
        microsecond: IntArg | None = None,
    ) -> datetime:
        """A copy with the given components replaced."""
        from .interactions import DatetimeReplace

        kw: dict[str, object] = {}
        for name, value in (
            ("year", year),
            ("month", month),
            ("day", day),
            ("hour", hour),
            ("minute", minute),
            ("second", second),
            ("microsecond", microsecond),
        ):
            if value is not None:
                kw[name] = value
        return datetime(DatetimeReplace(self, **kw))

    def __add__(self, other: TimedeltaArg) -> datetime:
        from nu.core import Add

        return datetime(Add(self, other))

    @overload
    def __sub__(self, other: datetime | _datetime) -> timedelta: ...
    @overload
    def __sub__(self, other: timedelta | _timedelta) -> datetime: ...
    def __sub__(self, other: DatetimeArg | TimedeltaArg) -> datetime | timedelta:
        from nu.core import Sub

        if isinstance(other, (datetime, _datetime)):
            return timedelta(Sub(self, other))
        return datetime(Sub(self, other))

    def __gt__(self, other: DatetimeArg) -> Bool:
        from nu.core import Gt
        from nu.forms import Bool

        return Bool(Gt(self, other))

    def __lt__(self, other: DatetimeArg) -> Bool:
        from nu.core import Lt
        from nu.forms import Bool

        return Bool(Lt(self, other))

    def __ge__(self, other: DatetimeArg) -> Bool:
        from nu.core import Ge
        from nu.forms import Bool

        return Bool(Ge(self, other))

    def __le__(self, other: DatetimeArg) -> Bool:
        from nu.core import Le
        from nu.forms import Bool

        return Bool(Le(self, other))

    def eq(self, other: DatetimeArg) -> Bool:
        """Whether two datetimes are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: DatetimeArg) -> Bool:
        """Whether two datetimes differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))


class timezone(Form, TypedNu[_timezone]):  # noqa: N801
    """``datetime.timezone`` as a Form - a fixed offset from UTC."""

    @classmethod
    def of(cls, offset: TimedeltaArg, name: StrArg | None = None) -> timezone:
        """Build a fixed-offset zone: ``timezone(offset, name)``."""
        from .interactions import TimezoneOf

        if name is not None:
            return timezone(TimezoneOf(offset, name))
        return timezone(TimezoneOf(offset))

    @classmethod
    def utc(cls) -> timezone:
        """The UTC zone: ``timezone.utc``."""
        from .interactions import TimezoneUtc

        return timezone(TimezoneUtc())

    def utcoffset(self, dt: DatetimeArg | None = None) -> timedelta:
        """The offset from UTC as a timedelta."""
        from .interactions import TimezoneUtcoffset

        return timedelta(TimezoneUtcoffset(self, dt))

    def tzname(self, dt: DatetimeArg | None = None) -> Str:
        """The zone's name."""
        from nu.forms import Str

        from .interactions import TimezoneTzname

        return Str(TimezoneTzname(self, dt))

    def dst(self, dt: DatetimeArg | None = None) -> None_:
        """Daylight-saving adjustment (always None for a fixed offset)."""
        from nu.forms import None_

        from .interactions import TimezoneDst

        return None_(TimezoneDst(self, dt))

    def eq(self, other: TimezoneArg) -> Bool:
        """Whether two zones are equal."""
        from nu.core import Eq
        from nu.forms import Bool

        return Bool(Eq(self, other))

    def ne(self, other: TimezoneArg) -> Bool:
        """Whether two zones differ."""
        from nu.core import Ne
        from nu.forms import Bool

        return Bool(Ne(self, other))
