"""Extended type system.

This module provides Type, Ref, and Slot implementations for common Python types
beyond the basic primitives (int, str, float, bool).

Available Types:
    Standard:
        - datetime: DatetimeType, DatetimeRef, DatetimeSlot
        - timedelta: TimedeltaType, TimedeltaRef, TimedeltaSlot
        - timezone: TimezoneType, TimezoneRef, TimezoneSlot
        - date: DateType, DateRef, DateSlot
        - time: TimeType, TimeRef, TimeSlot
        - Decimal: DecimalType, DecimalRef, DecimalSlot
        - Fraction: FractionType, FractionRef, FractionSlot
        - UUID: UUIDType, UUIDRef, UUIDSlot
        - Path: PathType, PathRef, PathSlot
        - complex: ComplexType, ComplexRef, ComplexSlot

    Financial:
        - BasisPoint: BasisPointType, BasisPointRef, BasisPointSlot
        - Percentage: PercentageType, PercentageRef, PercentageSlot

    Series:
        - Point, Series: Native Python classes
        - PointType, SeriesType, SeriesRef, SeriesSlot

Example:
    from everybase.shape import Shape
    from everybase.type import DatetimeSlot, DecimalSlot, UUIDSlot

    class Transaction(Shape):
        id = UUIDSlot()
        amount = DecimalSlot()
        timestamp = DatetimeSlot()

    # Usage in flows
    Transaction.id.set(uuid4())
    Transaction.amount.set(Decimal("100.50"))
    Transaction.timestamp.set(datetime.now())

    # Rich operations
    Transaction.timestamp.get().year()
    Transaction.amount.get() * Decimal("1.1")
"""

# Bases point module
from .bases_point import (
    BasisPoint,
    BasisPointRef,
    BasisPointSlot,
    BasisPointType,
)

# Complex module
from .complex import (
    ComplexRef,
    ComplexSlot,
    ComplexType,
)

# Date module
from .date import (
    DateRef,
    DateSlot,
    DateType,
)

# Datetime module
from .datetime import (
    DatetimeRef,
    DatetimeSlot,
    DatetimeType,
)

# Decimal module
from .decimal import (
    DecimalRef,
    DecimalSlot,
    DecimalType,
)

# Fraction module
from .fraction import (
    FractionRef,
    FractionSlot,
    FractionType,
)

# Path module
from .path import (
    PathRef,
    PathSlot,
    PathType,
)

# Percentage module
from .percentage import (
    Percentage,
    PercentageRef,
    PercentageSlot,
    PercentageType,
)

# Series module
from .series import (
    Point,
    PointType,
    Series,
    SeriesRef,
    SeriesSlot,
    SeriesType,
)

# Time module
from .time import (
    TimeRef,
    TimeSlot,
    TimeType,
)

# Timedelta module
from .timedelta import (
    TimedeltaRef,
    TimedeltaSlot,
    TimedeltaType,
)

# Timezone module
from .timezone import (
    TimezoneRef,
    TimezoneSlot,
    TimezoneType,
)

# UUID module
from .uuid import (
    UUIDRef,
    UUIDSlot,
    UUIDType,
)


__all__ = [
    # Basis Points (native class + Shape types)
    "BasisPoint",
    "BasisPointType",
    "BasisPointRef",
    "BasisPointSlot",
    # Complex (Shape types only - uses Python's complex)
    "ComplexType",
    "ComplexRef",
    "ComplexSlot",
    # Date (Shape types only - uses Python's date)
    "DateType",
    "DateRef",
    "DateSlot",
    # Datetime (Shape types only - uses Python's datetime)
    "DatetimeType",
    "DatetimeRef",
    "DatetimeSlot",
    # Decimal (Shape types only - uses Python's Decimal)
    "DecimalType",
    "DecimalRef",
    "DecimalSlot",
    # Fraction (Shape types only - uses Python's Fraction)
    "FractionType",
    "FractionRef",
    "FractionSlot",
    # Path (Shape types only - uses Python's Path)
    "PathType",
    "PathRef",
    "PathSlot",
    # Percentage (native class + Shape types)
    "Percentage",
    "PercentageType",
    "PercentageRef",
    "PercentageSlot",
    # Series (native classes + Shape types)
    "Point",
    "Series",
    "PointType",
    "SeriesType",
    "SeriesRef",
    "SeriesSlot",
    # Time (Shape types only - uses Python's time)
    "TimeType",
    "TimeRef",
    "TimeSlot",
    # Timedelta (Shape types only - uses Python's timedelta)
    "TimedeltaType",
    "TimedeltaRef",
    "TimedeltaSlot",
    # Timezone (Shape types only - uses Python's timezone)
    "TimezoneType",
    "TimezoneRef",
    "TimezoneSlot",
    # UUID (Shape types only - uses Python's UUID)
    "UUIDType",
    "UUIDRef",
    "UUIDSlot",
]
