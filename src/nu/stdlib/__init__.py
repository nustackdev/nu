"""Nu standard library - typed interfaces for Python stdlib types.

Modules mirror Python's stdlib naming:
    datetime    date, datetime, time, timedelta, timezone
    uuid        UUID
    decimal     Decimal
    fractions   Fraction
    cmath       complex
    pathlib     Path
    fin         Percentage, BasisPoint (financial types)
"""

from __future__ import annotations

from .cmath import ComplexArg, ComplexI
from .datetime import (
    DateArg,
    DateI,
    DatetimeArg,
    DatetimeI,
    TimeArg,
    TimeI,
    TimedeltaArg,
    TimedeltaI,
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
from .uuid import UUIDArg, UUIDI


__all__ = [
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
    "TimedeltaArg",
    "TimedeltaI",
    "TimezoneArg",
    "TimezoneI",
    "UUIDArg",
    "UUIDI",
]
