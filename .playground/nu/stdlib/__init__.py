"""Nu standard library - typed interfaces for Python stdlib types.

Modules mirror Python's stdlib naming:
    datetime    date, datetime, time, timedelta, timezone
    uuid        UUID
    decimal     Decimal
    fractions   Fraction
    cmath       complex
    pathlib     Path
    fin         Percentage, BasisPoint (financial types)
    asyncio     AsyncSleep  (ASYNC)
    time        TimeSleep   (SYNC)
"""

from __future__ import annotations

from .asyncio import AsyncSleep
from .cmath import ComplexArg, ComplexI
from .datetime import (
    DateArg,
    DateI,
    DatetimeArg,
    DatetimeI,
    TimeArg,
    TimedeltaArg,
    TimedeltaI,
    TimeI,
    TimezoneArg,
    TimezoneI,
)
from .decimal import DecimalArg, DecimalI
from .fin import (
    BasisPoint,
    BasisPointArg,
    BasisPointI,
    Percentage,
    PercentageArg,
    PercentageI,
)
from .fractions import FractionArg, FractionI
from .pathlib import PathArg, PathI
from .time import TimeSleep
from .uuid import UUIDI, UUIDArg


__all__ = [
    "UUIDI",
    "AsyncSleep",
    "BasisPoint",
    "BasisPointArg",
    "BasisPointI",
    "ComplexArg",
    "ComplexI",
    "DateArg",
    "DateI",
    "DatetimeArg",
    "DatetimeI",
    "DecimalArg",
    "DecimalI",
    "FractionArg",
    "FractionI",
    "PathArg",
    "PathI",
    "Percentage",
    "PercentageArg",
    "PercentageI",
    "TimeArg",
    "TimeI",
    "TimeSleep",
    "TimedeltaArg",
    "TimedeltaI",
    "TimezoneArg",
    "TimezoneI",
    "UUIDArg",
]
