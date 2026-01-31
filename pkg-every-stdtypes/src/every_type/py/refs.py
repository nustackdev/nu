"""Python memory refs for standard library types.

These refs combine PyRefBase (substrate) with *RefBase (type interface).
Pattern: XxxRef = PyRefBase[Xxx] + XxxRefBase
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

from everybase.py import PyRefBase

from ..basis_point_cls import BasisPoint
from ..basis_point_ref import BasisPointRefBase
from ..complex_ref import ComplexRefBase
from ..date_ref import DateRefBase
from ..datetime_ref import DatetimeRefBase
from ..decimal_ref import DecimalRefBase
from ..fraction_ref import FractionRefBase
from ..path_ref import PathRefBase
from ..percentage_cls import Percentage
from ..percentage_ref import PercentageRefBase
from ..time_ref import TimeRefBase
from ..timedelta_ref import TimedeltaRefBase
from ..timezone_ref import TimezoneRefBase
from ..uuid_ref import UUIDRefBase


__all__ = [
    "BasisPointRef",
    "ComplexRef",
    # Datetime
    "DateRef",
    "DatetimeRef",
    # Numeric
    "DecimalRef",
    "FractionRef",
    # Path and UUID
    "PathRef",
    "PercentageRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
]


# =============================================================================
# NUMERIC REFS
# =============================================================================


class DecimalRef(PyRefBase[Decimal], DecimalRefBase):
    """Python memory ref for Decimal values.

    Inherits:
    - PyRefBase[Decimal]: source storage, fetch() implementation
    - DecimalRefBase: arithmetic, comparison, decimal methods
    """

    pass


class FractionRef(PyRefBase[Fraction], FractionRefBase):
    """Python memory ref for Fraction values.

    Inherits:
    - PyRefBase[Fraction]: source storage, fetch() implementation
    - FractionRefBase: arithmetic, comparison, fraction methods
    """

    pass


class ComplexRef(PyRefBase[complex], ComplexRefBase):
    """Python memory ref for complex values.

    Inherits:
    - PyRefBase[complex]: source storage, fetch() implementation
    - ComplexRefBase: arithmetic, equality, complex methods
    """

    pass


class BasisPointRef(PyRefBase[BasisPoint], BasisPointRefBase):
    """Python memory ref for BasisPoint values.

    Inherits:
    - PyRefBase[BasisPoint]: source storage, fetch() implementation
    - BasisPointRefBase: arithmetic, comparison, basis point methods
    """

    pass


class PercentageRef(PyRefBase[Percentage], PercentageRefBase):
    """Python memory ref for Percentage values.

    Inherits:
    - PyRefBase[Percentage]: source storage, fetch() implementation
    - PercentageRefBase: arithmetic, comparison, percentage methods
    """

    pass


# =============================================================================
# DATETIME REFS
# =============================================================================


class DateRef(PyRefBase[date], DateRefBase):
    """Python memory ref for date values.

    Inherits:
    - PyRefBase[date]: source storage, fetch() implementation
    - DateRefBase: comparison, date methods, date arithmetic
    """

    pass


class DatetimeRef(PyRefBase[datetime], DatetimeRefBase):
    """Python memory ref for datetime values.

    Inherits:
    - PyRefBase[datetime]: source storage, fetch() implementation
    - DatetimeRefBase: comparison, datetime methods, datetime arithmetic
    """

    pass


class TimeRef(PyRefBase[time], TimeRefBase):
    """Python memory ref for time values.

    Inherits:
    - PyRefBase[time]: source storage, fetch() implementation
    - TimeRefBase: comparison, time methods
    """

    pass


class TimedeltaRef(PyRefBase[timedelta], TimedeltaRefBase):
    """Python memory ref for timedelta values.

    Inherits:
    - PyRefBase[timedelta]: source storage, fetch() implementation
    - TimedeltaRefBase: comparison, arithmetic, timedelta methods
    """

    pass


class TimezoneRef(PyRefBase[timezone], TimezoneRefBase):
    """Python memory ref for timezone values.

    Inherits:
    - PyRefBase[timezone]: source storage, fetch() implementation
    - TimezoneRefBase: equality, timezone methods
    """

    pass


# =============================================================================
# PATH AND UUID REFS
# =============================================================================


class PathRef(PyRefBase[Path], PathRefBase):
    """Python memory ref for Path values.

    Inherits:
    - PyRefBase[Path]: source storage, fetch() implementation
    - PathRefBase: comparison, path manipulation methods
    """

    pass


class UUIDRef(PyRefBase[UUID], UUIDRefBase):
    """Python memory ref for UUID values.

    Inherits:
    - PyRefBase[UUID]: source storage, fetch() implementation
    - UUIDRefBase: comparison, UUID methods
    """

    pass
