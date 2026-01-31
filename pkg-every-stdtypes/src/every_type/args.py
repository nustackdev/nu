"""Type argument aliases for standard library types.

These are used in function signatures to accept both Python values and Ref types.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path, PurePath
from typing import TYPE_CHECKING
from uuid import UUID

from everyabc import Arg


if TYPE_CHECKING:
    from .basis_point_cls import BasisPoint
    from .percentage_cls import Percentage

__all__ = [
    "BasisPointArg",
    "ComplexArg",
    # Datetime
    "DateArg",
    "DatetimeArg",
    # Numeric
    "DecimalArg",
    "FractionArg",
    # Path and UUID
    "PathArg",
    "PercentageArg",
    "TimeArg",
    "TimedeltaArg",
    "TimezoneArg",
    "UUIDArg",
]

# =============================================================================
# NUMERIC ARGS
# =============================================================================

type DecimalArg = Arg[Decimal | int | float | str]
type FractionArg = Arg[Fraction | int | float | str]
type ComplexArg = Arg[complex | int | float]
type BasisPointArg = Arg["BasisPoint | int"]
type PercentageArg = Arg["Percentage | float"]

# =============================================================================
# DATETIME ARGS
# =============================================================================

type DateArg = Arg[date]
type DatetimeArg = Arg[datetime]
type TimeArg = Arg[time]
type TimedeltaArg = Arg[timedelta]
type TimezoneArg = Arg[timezone]

# =============================================================================
# PATH AND UUID ARGS
# =============================================================================

type PathArg = Arg[Path | PurePath | str]
type UUIDArg = Arg[UUID | str]
