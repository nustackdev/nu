"""Standard library type refs for everybase.

This package provides refs for common Python standard library types:
- Numeric: Decimal, Fraction, complex, BasisPoint, Percentage
- Datetime: date, datetime, time, timedelta, timezone
- Other: Path, UUID

Each type has:
- *RefBase: Abstract base with type operations (e.g., DecimalRefBase)
- *Ref: Python memory ref (e.g., DecimalRef in py/)
- PV*Ref: PV storage ref with serialization (e.g., PVDecimalRef in pv/)
- *Slot: Slot factory for Shape fields (e.g., DecimalSlot in pv/)

Example usage:
    from every_type import DecimalRef, UUIDRef
    from every_type.pv import PVDecimalRef, DecimalSlot

    # Python memory ref
    d = DecimalRef.from_str("123.456")
    result = d + DecimalRef.from_str("0.001")

    # PV storage in Shape
    from every import Shape

    class Account(Shape):
        balance: PVDecimalRef = DecimalSlot()
        id: PVUUIDRef = UUIDSlot()
"""

# Args
from .args import (
    BasisPointArg,
    ComplexArg,
    DateArg,
    DatetimeArg,
    DecimalArg,
    FractionArg,
    PathArg,
    PercentageArg,
    TimeArg,
    TimedeltaArg,
    TimezoneArg,
    UUIDArg,
)

# Custom Python classes
from .basis_point_cls import BasisPoint

# RefBase classes
from .basis_point_ref import BasisPointRefBase
from .complex_ref import ComplexRefBase
from .date_ref import DateRefBase
from .datetime_ref import DatetimeRefBase
from .decimal_ref import DecimalRefBase
from .fraction_ref import FractionRefBase
from .path_ref import PathRefBase
from .percentage_cls import Percentage
from .percentage_ref import PercentageRefBase

# Python memory refs
from .py import (
    BasisPointRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    FractionRef,
    PathRef,
    PercentageRef,
    TimedeltaRef,
    TimeRef,
    TimezoneRef,
    UUIDRef,
)
from .time_ref import TimeRefBase
from .timedelta_ref import TimedeltaRefBase
from .timezone_ref import TimezoneRefBase
from .uuid_ref import UUIDRefBase


__all__ = [
    # Custom Python classes
    "BasisPoint",
    "BasisPointArg",
    "BasisPointRef",
    "BasisPointRefBase",
    "ComplexArg",
    "ComplexRef",
    "ComplexRefBase",
    "DateArg",
    "DateRef",
    "DateRefBase",
    "DatetimeArg",
    "DatetimeRef",
    "DatetimeRefBase",
    # Args
    "DecimalArg",
    # Python memory refs
    "DecimalRef",
    # RefBase classes
    "DecimalRefBase",
    "FractionArg",
    "FractionRef",
    "FractionRefBase",
    "PathArg",
    "PathRef",
    "PathRefBase",
    "Percentage",
    "PercentageArg",
    "PercentageRef",
    "PercentageRefBase",
    "TimeArg",
    "TimeRef",
    "TimeRefBase",
    "TimedeltaArg",
    "TimedeltaRef",
    "TimedeltaRefBase",
    "TimezoneArg",
    "TimezoneRef",
    "TimezoneRefBase",
    "UUIDArg",
    "UUIDRef",
    "UUIDRefBase",
]
