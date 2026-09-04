"""datetime interactions - one ``host`` binding per host call.

Constructors bind a class / classmethod; methods bind the *unbound* method (a
plain callable whose first argument is the receiver, so ``d.weekday()`` is
``date.weekday(d)``). Property reads (``.year``, ``.hour``, ``.days`` ...) are
not here - they reuse core ``GetAttr`` from the Form. Arithmetic and
comparison reuse the core atoms.

``DateToday`` / ``DatetimeNow`` read the clock. The ``*FromTimestamp``
constructors take an explicit timestamp, so they are pure functions of their
args.
"""

from __future__ import annotations

from datetime import date as _date
from datetime import datetime as _datetime
from datetime import time as _time
from datetime import timedelta as _timedelta
from datetime import timezone as _timezone

from nu.factory import host


UTC = _timezone.utc


__all__ = [
    "DateCtime",
    "DateFromIso",
    "DateFromOrdinal",
    "DateFromTimestamp",
    "DateIsoformat",
    "DateIsoweekday",
    "DateOf",
    "DateReplace",
    "DateStrftime",
    "DateToday",
    "DateToordinal",
    "DateWeekday",
    "DatetimeCombine",
    "DatetimeDate",
    "DatetimeFromIso",
    "DatetimeFromTimestamp",
    "DatetimeIsoformat",
    "DatetimeIsoweekday",
    "DatetimeNow",
    "DatetimeOf",
    "DatetimeReplace",
    "DatetimeStrftime",
    "DatetimeTime",
    "DatetimeTimestamp",
    "DatetimeWeekday",
    "TimeFromIso",
    "TimeIsoformat",
    "TimeOf",
    "TimeReplace",
    "TimeStrftime",
    "TimedeltaTotalSeconds",
    "TimezoneDst",
    "TimezoneOf",
    "TimezoneTzname",
    "TimezoneUtc",
    "TimezoneUtcoffset",
]


# --- date -------------------------------------------------------------------

DateOf = host(_date, name="DateOf")
DateToday = host(_date.today, name="DateToday")
DateFromIso = host(_date.fromisoformat, name="DateFromIso")
DateFromOrdinal = host(_date.fromordinal, name="DateFromOrdinal")
DateFromTimestamp = host(_date.fromtimestamp, name="DateFromTimestamp")
DateWeekday = host(_date.weekday, name="DateWeekday")
DateIsoweekday = host(_date.isoweekday, name="DateIsoweekday")
DateToordinal = host(_date.toordinal, name="DateToordinal")
DateIsoformat = host(_date.isoformat, name="DateIsoformat")
DateCtime = host(_date.ctime, name="DateCtime")
DateStrftime = host(_date.strftime, name="DateStrftime")
DateReplace = host(_date.replace, name="DateReplace")

# --- time -------------------------------------------------------------------

TimeOf = host(_time, name="TimeOf")
TimeFromIso = host(_time.fromisoformat, name="TimeFromIso")
TimeIsoformat = host(_time.isoformat, name="TimeIsoformat")
TimeStrftime = host(_time.strftime, name="TimeStrftime")
TimeReplace = host(_time.replace, name="TimeReplace")

# --- datetime ---------------------------------------------------------------

DatetimeOf = host(_datetime, name="DatetimeOf")
DatetimeNow = host(_datetime.now, name="DatetimeNow")
DatetimeFromIso = host(_datetime.fromisoformat, name="DatetimeFromIso")
DatetimeFromTimestamp = host(_datetime.fromtimestamp, name="DatetimeFromTimestamp")
DatetimeCombine = host(_datetime.combine, name="DatetimeCombine")
DatetimeWeekday = host(_datetime.weekday, name="DatetimeWeekday")
DatetimeIsoweekday = host(_datetime.isoweekday, name="DatetimeIsoweekday")
DatetimeTimestamp = host(_datetime.timestamp, name="DatetimeTimestamp")
DatetimeIsoformat = host(_datetime.isoformat, name="DatetimeIsoformat")
DatetimeStrftime = host(_datetime.strftime, name="DatetimeStrftime")
DatetimeDate = host(_datetime.date, name="DatetimeDate")
DatetimeTime = host(_datetime.time, name="DatetimeTime")
DatetimeReplace = host(_datetime.replace, name="DatetimeReplace")

# --- timedelta --------------------------------------------------------------

TimedeltaOf = host(_timedelta, name="TimedeltaOf")
TimedeltaTotalSeconds = host(_timedelta.total_seconds, name="TimedeltaTotalSeconds")

# --- timezone ---------------------------------------------------------------

TimezoneOf = host(_timezone, name="TimezoneOf")
TimezoneUtc = host(lambda: UTC, name="TimezoneUtc")
TimezoneUtcoffset = host(_timezone.utcoffset, name="TimezoneUtcoffset")
TimezoneTzname = host(_timezone.tzname, name="TimezoneTzname")
TimezoneDst = host(_timezone.dst, name="TimezoneDst")
