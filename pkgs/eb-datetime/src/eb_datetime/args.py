"""Type argument aliases for datetime types."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from everybase import Arg


__all__ = [
    "DateArg",
    "DatetimeArg",
    "TimeArg",
    "TimedeltaArg",
    "TimezoneArg",
]

type DateArg = Arg[date]
type DatetimeArg = Arg[datetime]
type TimeArg = Arg[time]
type TimedeltaArg = Arg[timedelta]
type TimezoneArg = Arg[timezone]
