"""PV storage refs for standard library types.

These refs store values in PV storage with serialization/deserialization.
Pattern: PVXxxRef = PVPrimitiveRef[StorageType] + XxxRefBase + get/set methods

Storage formats:
- Decimal: str (exact representation)
- Fraction: str ("numerator/denominator")
- Complex: str ("real,imag")
- BasisPoint: int (raw basis points)
- Percentage: float (raw percentage)
- Date: str (ISO format YYYY-MM-DD)
- Datetime: str (ISO format)
- Time: str (ISO format HH:MM:SS[.ffffff])
- Timedelta: float (total_seconds)
- Timezone: str (offset like "+05:30")
- Path: str
- UUID: str (hex format)
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from every_pv.ref import PVPrimitiveRef

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
from ..py.refs import (
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
from ..time_ref import TimeRefBase
from ..timedelta_ref import TimedeltaRefBase
from ..timezone_ref import TimezoneRefBase
from ..uuid_ref import UUIDRefBase


if TYPE_CHECKING:
    from pv.loc import path

    from every import Shape, Term


__all__ = [
    "PVBasisPointRef",
    "PVComplexRef",
    # Datetime
    "PVDateRef",
    "PVDatetimeRef",
    # Numeric
    "PVDecimalRef",
    "PVFractionRef",
    # Path and UUID
    "PVPathRef",
    "PVPercentageRef",
    "PVTimeRef",
    "PVTimedeltaRef",
    "PVTimezoneRef",
    "PVUUIDRef",
]


# =============================================================================
# NUMERIC PV REFS
# =============================================================================


class PVDecimalRef(PVPrimitiveRef[str], DecimalRefBase):
    """PV storage ref for Decimal values.

    Stores as str for exact representation.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> DecimalRef:
        """Get the Decimal value."""
        return DecimalRef.from_str(self)

    def set(self, value: Decimal | str | DecimalRef) -> DecimalRef:
        """Set the Decimal value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, Decimal):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return DecimalRef(TypedSetCmd(self, val))


class PVFractionRef(PVPrimitiveRef[str], FractionRefBase):
    """PV storage ref for Fraction values.

    Stores as str ("numerator/denominator" format).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> FractionRef:
        """Get the Fraction value."""
        return FractionRef.from_str(self)

    def set(self, value: Fraction | str | FractionRef) -> FractionRef:
        """Set the Fraction value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, Fraction):
            val = f"{value.numerator}/{value.denominator}"
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return FractionRef(TypedSetCmd(self, val))


class PVComplexRef(PVPrimitiveRef[str], ComplexRefBase):
    """PV storage ref for complex values.

    Stores as str ("real,imag" format).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> ComplexRef:
        """Get the complex value."""
        # Parse "real,imag" format
        from everybase.morphisms import FuncCallOp

        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexRef(FuncCallOp(parse_complex, self))

    def set(self, value: complex | str | ComplexRef) -> ComplexRef:
        """Set the complex value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import FuncCallOp

        if isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        elif isinstance(value, str):
            val = value
        else:
            # Format as "real,imag"
            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCallOp(format_complex, value)
        return ComplexRef(TypedSetCmd(self, val))


class PVBasisPointRef(PVPrimitiveRef[int], BasisPointRefBase):
    """PV storage ref for BasisPoint values.

    Stores as int (raw basis points).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, int, parent, shape)

    def get(self) -> BasisPointRef:
        """Get the BasisPoint value."""
        return BasisPointRef.from_int(self)

    def set(self, value: BasisPoint | int | BasisPointRef) -> BasisPointRef:
        """Set the BasisPoint value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, BasisPoint):
            val = value.value
        elif isinstance(value, int):
            val = value
        else:
            val = MethodCallOp(value, "to_int")
        return BasisPointRef(TypedSetCmd(self, val))


class PVPercentageRef(PVPrimitiveRef[float], PercentageRefBase):
    """PV storage ref for Percentage values.

    Stores as float (raw percentage value).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, float, parent, shape)

    def get(self) -> PercentageRef:
        """Get the Percentage value."""
        return PercentageRef.from_float(self)

    def set(self, value: Percentage | float | PercentageRef) -> PercentageRef:
        """Set the Percentage value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, Percentage):
            val = value.value
        elif isinstance(value, (int, float)):
            val = float(value)
        else:
            val = MethodCallOp(value, "to_float")
        return PercentageRef(TypedSetCmd(self, val))


# =============================================================================
# DATETIME PV REFS
# =============================================================================


class PVDateRef(PVPrimitiveRef[str], DateRefBase):
    """PV storage ref for date values.

    Stores as str (ISO format YYYY-MM-DD).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> DateRef:
        """Get the date value."""
        return DateRef.from_iso(self)

    def set(self, value: date | str | DateRef) -> DateRef:
        """Set the date value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, date):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "isoformat")
        return DateRef(TypedSetCmd(self, val))


class PVDatetimeRef(PVPrimitiveRef[str], DatetimeRefBase):
    """PV storage ref for datetime values.

    Stores as str (ISO format).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> DatetimeRef:
        """Get the datetime value."""
        return DatetimeRef.from_iso(self)

    def set(self, value: datetime | str | DatetimeRef) -> DatetimeRef:
        """Set the datetime value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, datetime):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "isoformat")
        return DatetimeRef(TypedSetCmd(self, val))


class PVTimeRef(PVPrimitiveRef[str], TimeRefBase):
    """PV storage ref for time values.

    Stores as str (ISO format HH:MM:SS[.ffffff]).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> TimeRef:
        """Get the time value."""
        return TimeRef.from_iso(self)

    def set(self, value: time | str | TimeRef) -> TimeRef:
        """Set the time value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, time):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "isoformat")
        return TimeRef(TypedSetCmd(self, val))


class PVTimedeltaRef(PVPrimitiveRef[float], TimedeltaRefBase):
    """PV storage ref for timedelta values.

    Stores as float (total_seconds).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, float, parent, shape)

    def get(self) -> TimedeltaRef:
        """Get the timedelta value."""
        return TimedeltaRef.from_seconds(self)

    def set(self, value: timedelta | float | TimedeltaRef) -> TimedeltaRef:
        """Set the timedelta value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, timedelta):
            val = value.total_seconds()
        elif isinstance(value, (int, float)):
            val = float(value)
        else:
            val = MethodCallOp(value, "total_seconds")
        return TimedeltaRef(TypedSetCmd(self, val))


class PVTimezoneRef(PVPrimitiveRef[str], TimezoneRefBase):
    """PV storage ref for timezone values.

    Stores as str (offset like "+05:30" or "UTC").
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> TimezoneRef:
        """Get the timezone value."""
        from everybase.morphisms import FuncCallOp

        def parse_timezone(s: str) -> timezone:
            if s == "UTC":
                from datetime import UTC

                return UTC
            # Parse offset format like "+05:30" or "-08:00"
            sign = 1 if s[0] == "+" else -1
            parts = s[1:].split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

        return TimezoneRef(FuncCallOp(parse_timezone, self))

    def set(self, value: timezone | str | TimezoneRef) -> TimezoneRef:
        """Set the timezone value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import FuncCallOp

        if isinstance(value, timezone):
            from datetime import UTC

            if value == UTC:
                val = "UTC"
            else:
                offset = value.utcoffset(None)
                total_seconds = int(offset.total_seconds())
                sign = "+" if total_seconds >= 0 else "-"
                total_seconds = abs(total_seconds)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                val = f"{sign}{hours:02d}:{minutes:02d}"
        elif isinstance(value, str):
            val = value
        else:

            def format_timezone(tz: timezone) -> str:
                from datetime import UTC

                if tz == UTC:
                    return "UTC"
                offset = tz.utcoffset(None)
                total_seconds = int(offset.total_seconds())
                sign = "+" if total_seconds >= 0 else "-"
                total_seconds = abs(total_seconds)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{sign}{hours:02d}:{minutes:02d}"

            val = FuncCallOp(format_timezone, value)
        return TimezoneRef(TypedSetCmd(self, val))


# =============================================================================
# PATH AND UUID PV REFS
# =============================================================================


class PVPathRef(PVPrimitiveRef[str], PathRefBase):
    """PV storage ref for Path values.

    Stores as str.
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> PathRef:
        """Get the Path value."""
        return PathRef.from_str(self)

    def set(self, value: Path | str | PathRef) -> PathRef:
        """Set the Path value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, Path):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return PathRef(TypedSetCmd(self, val))


class PVUUIDRef(PVPrimitiveRef[str], UUIDRefBase):
    """PV storage ref for UUID values.

    Stores as str (hex format).
    """

    def __init__(
        self,
        address: path.PathAddress | Term,
        parent: PVPrimitiveRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, str, parent, shape)

    def get(self) -> UUIDRef:
        """Get the UUID value."""
        return UUIDRef.from_str(self)

    def set(self, value: UUID | str | UUIDRef) -> UUIDRef:
        """Set the UUID value."""
        from every_pv.morphisms import TypedSetCmd
        from everybase.morphisms import MethodCallOp

        if isinstance(value, UUID):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return UUIDRef(TypedSetCmd(self, val))
