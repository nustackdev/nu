"""datetime interactions - one ``ScalarQueryFactory`` binding per host call.

Constructors bind a class / classmethod; methods bind the *unbound* method (a
plain callable whose first argument is the receiver, so ``d.weekday()`` is
``date.weekday(d)``). Property reads (``.year``, ``.hour``, ``.days`` ...) are
not here - they reuse core ``GetAttrQuery`` from the Form. Arithmetic and
comparison reuse the core atoms.

``DateToday`` / ``DatetimeNow`` read the clock, so they declare
``deterministic=False`` to stay un-folded. The ``*FromTimestamp`` constructors
take an explicit timestamp, so they are deterministic functions of their args.
"""

from __future__ import annotations

from datetime import UTC
from datetime import date as _date
from datetime import datetime as _datetime
from datetime import time as _time
from datetime import timedelta as _timedelta
from datetime import timezone as _timezone

from nu.lang import ScalarQueryFactory


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

DateOf = ScalarQueryFactory("DateOf", _date)
DateToday = ScalarQueryFactory("DateToday", _date.today, deterministic=False)
DateFromIso = ScalarQueryFactory("DateFromIso", _date.fromisoformat)
DateFromOrdinal = ScalarQueryFactory("DateFromOrdinal", _date.fromordinal)
DateFromTimestamp = ScalarQueryFactory("DateFromTimestamp", _date.fromtimestamp)
DateWeekday = ScalarQueryFactory("DateWeekday", _date.weekday)
DateIsoweekday = ScalarQueryFactory("DateIsoweekday", _date.isoweekday)
DateToordinal = ScalarQueryFactory("DateToordinal", _date.toordinal)
DateIsoformat = ScalarQueryFactory("DateIsoformat", _date.isoformat)
DateCtime = ScalarQueryFactory("DateCtime", _date.ctime)
DateStrftime = ScalarQueryFactory("DateStrftime", _date.strftime)
DateReplace = ScalarQueryFactory("DateReplace", _date.replace)

# --- time -------------------------------------------------------------------

TimeOf = ScalarQueryFactory("TimeOf", _time)
TimeFromIso = ScalarQueryFactory("TimeFromIso", _time.fromisoformat)
TimeIsoformat = ScalarQueryFactory("TimeIsoformat", _time.isoformat)
TimeStrftime = ScalarQueryFactory("TimeStrftime", _time.strftime)
TimeReplace = ScalarQueryFactory("TimeReplace", _time.replace)

# --- datetime ---------------------------------------------------------------

DatetimeOf = ScalarQueryFactory("DatetimeOf", _datetime)
DatetimeNow = ScalarQueryFactory("DatetimeNow", _datetime.now, deterministic=False)
DatetimeFromIso = ScalarQueryFactory("DatetimeFromIso", _datetime.fromisoformat)
DatetimeFromTimestamp = ScalarQueryFactory("DatetimeFromTimestamp", _datetime.fromtimestamp)
DatetimeCombine = ScalarQueryFactory("DatetimeCombine", _datetime.combine)
DatetimeWeekday = ScalarQueryFactory("DatetimeWeekday", _datetime.weekday)
DatetimeIsoweekday = ScalarQueryFactory("DatetimeIsoweekday", _datetime.isoweekday)
DatetimeTimestamp = ScalarQueryFactory("DatetimeTimestamp", _datetime.timestamp)
DatetimeIsoformat = ScalarQueryFactory("DatetimeIsoformat", _datetime.isoformat)
DatetimeStrftime = ScalarQueryFactory("DatetimeStrftime", _datetime.strftime)
DatetimeDate = ScalarQueryFactory("DatetimeDate", _datetime.date)
DatetimeTime = ScalarQueryFactory("DatetimeTime", _datetime.time)
DatetimeReplace = ScalarQueryFactory("DatetimeReplace", _datetime.replace)

# --- timedelta --------------------------------------------------------------

TimedeltaOf = ScalarQueryFactory("TimedeltaOf", _timedelta)
TimedeltaTotalSeconds = ScalarQueryFactory("TimedeltaTotalSeconds", _timedelta.total_seconds)

# --- timezone ---------------------------------------------------------------

TimezoneOf = ScalarQueryFactory("TimezoneOf", _timezone)
TimezoneUtc = ScalarQueryFactory("TimezoneUtc", lambda: UTC)
TimezoneUtcoffset = ScalarQueryFactory("TimezoneUtcoffset", _timezone.utcoffset)
TimezoneTzname = ScalarQueryFactory("TimezoneTzname", _timezone.tzname)
TimezoneDst = ScalarQueryFactory("TimezoneDst", _timezone.dst)
