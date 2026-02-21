"""PV storage refs for standard library types.

These refs store values in PV storage with serialization/deserialization.
Pattern: PV*Ref = ItemRef[StorageType, StrValue] + *Type + get/set methods

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

from eb_datetime import (
    DatetimeType,
    DatetimeValue,
    DateType,
    DateValue,
    TimedeltaType,
    TimedeltaValue,
    TimeType,
    TimeValue,
    TimezoneType,
    TimezoneValue,
)
from eb_fin import (
    BasisPoint,
    BasisPointType,
    BasisPointValue,
    Percentage,
    PercentageType,
    PercentageValue,
)
from eb_math import (
    ComplexType,
    ComplexValue,
    DecimalType,
    DecimalValue,
    FractionType,
    FractionValue,
)
from eb_path import PathType, PathValue
from eb_uuid import UUIDType, UUIDValue
from everybase import Term
from everybase.abc import FloatValue, FuncCallOp, IntValue, MethodCallOp, StrValue, ensure_term
from everyshape import Slot
from everyshape.morphisms import ItemSetCmd

from .items import ItemRef


if TYPE_CHECKING:
    from typing import Self

    from pv.loc import path

    from everyshape import Shape

    from .base import ViewRef


__all__ = [
    "BasisPointRef",
    "ComplexRef",
    "DateRef",
    "DatetimeRef",
    "DecimalRef",
    "FractionRef",
    "PathRef",
    "PercentageRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
]


# =============================================================================
# NUMERIC PV REFS
# =============================================================================


class DecimalRef(ItemRef[str, StrValue], DecimalType):
    """PV storage ref for Decimal values. Stores as str."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for Decimal values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> DecimalValue:
        """Get the Decimal value."""
        return DecimalValue.from_str(self)

    def set(self, value: Decimal | str | DecimalType) -> DecimalValue:
        """Set the Decimal value."""
        if isinstance(value, Decimal):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return DecimalValue(ItemSetCmd(self, ensure_term(val)))


class FractionRef(ItemRef[str, StrValue], FractionType):
    """PV storage ref for Fraction values. Stores as str."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for Fraction values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> FractionValue:
        """Get the Fraction value."""
        return FractionValue.from_str(self)

    def set(self, value: Fraction | str | FractionType) -> FractionValue:
        """Set the Fraction value."""
        if isinstance(value, Fraction):
            val = f"{value.numerator}/{value.denominator}"
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return FractionValue(ItemSetCmd(self, ensure_term(val)))


class ComplexRef(ItemRef[str, StrValue], ComplexType):
    """PV storage ref for complex values. Stores as str ("real,imag")."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for complex values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> ComplexValue:
        """Get the complex value."""

        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexValue(FuncCallOp(parse_complex, self))

    def set(self, value: complex | str | ComplexType) -> ComplexValue:
        """Set the complex value."""
        if isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        elif isinstance(value, str):
            val = value
        else:

            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCallOp(format_complex, value)
        return ComplexValue(ItemSetCmd(self, ensure_term(val)))


class BasisPointRef(ItemRef[int, IntValue], BasisPointType):
    """PV storage ref for BasisPoint values. Stores as int."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for BasisPoint values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> BasisPointValue:
        """Get the BasisPoint value."""
        return BasisPointValue.from_int(self)

    def set(self, value: BasisPoint | int | BasisPointType) -> BasisPointValue:
        """Set the BasisPoint value."""
        if isinstance(value, BasisPoint):
            val = value.value
        elif isinstance(value, int):
            val = value
        else:
            val = MethodCallOp(value, "to_int")
        return BasisPointValue(ItemSetCmd(self, ensure_term(val)))


class PercentageRef(ItemRef[float, FloatValue], PercentageType):
    """PV storage ref for Percentage values. Stores as float."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for Percentage values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> PercentageValue:
        """Get the Percentage value."""
        return PercentageValue.from_float(self)

    def set(self, value: Percentage | float | PercentageType) -> PercentageValue:
        """Set the Percentage value."""
        if isinstance(value, Percentage):
            val = value.value
        elif isinstance(value, (int, float)):
            val = float(value)
        else:
            val = MethodCallOp(value, "to_float")
        return PercentageValue(ItemSetCmd(self, ensure_term(val)))


# =============================================================================
# DATETIME PV REFS
# =============================================================================


class DateRef(ItemRef[str, StrValue], DateType):
    """PV storage ref for date values. Stores as str (ISO format)."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for date values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> DateValue:
        """Get the date value."""
        return DateValue.from_iso(self)

    def set(self, value: date | str | DateType) -> DateValue:
        """Set the date value."""
        if isinstance(value, date):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        elif isinstance(value, Term):
            val = value  # PV ref — already stores as ISO string
        else:
            val = MethodCallOp(value, "isoformat")
        return DateValue(ItemSetCmd(self, ensure_term(val)))


class DatetimeRef(ItemRef[str, StrValue], DatetimeType):
    """PV storage ref for datetime values. Stores as str (ISO format)."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for datetime values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> DatetimeValue:
        """Get the datetime value."""
        return DatetimeValue.from_iso(self)

    def set(self, value: datetime | str | DatetimeType) -> DatetimeValue:
        """Set the datetime value."""
        if isinstance(value, datetime):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        elif isinstance(value, Term):
            val = value  # PV ref — already stores as ISO string
        else:
            val = MethodCallOp(value, "isoformat")
        return DatetimeValue(ItemSetCmd(self, ensure_term(val)))


class TimeRef(ItemRef[str, StrValue], TimeType):
    """PV storage ref for time values. Stores as str (ISO format)."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for time values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> TimeValue:
        """Get the time value."""
        return TimeValue.from_iso(self)

    def set(self, value: time | str | TimeType) -> TimeValue:
        """Set the time value."""
        if isinstance(value, time):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        elif isinstance(value, Term):
            val = value  # PV ref — already stores as ISO string
        else:
            val = MethodCallOp(value, "isoformat")
        return TimeValue(ItemSetCmd(self, ensure_term(val)))


class TimedeltaRef(ItemRef[float, FloatValue], TimedeltaType):
    """PV storage ref for timedelta values. Stores as float (seconds)."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for timedelta values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> TimedeltaValue:
        """Get the timedelta value."""
        return TimedeltaValue.from_seconds(self)

    def set(self, value: timedelta | float | TimedeltaType) -> TimedeltaValue:
        """Set the timedelta value."""
        if isinstance(value, timedelta):
            val = value.total_seconds()
        elif isinstance(value, (int, float)):
            val = float(value)
        else:
            val = MethodCallOp(value, "total_seconds")
        return TimedeltaValue(ItemSetCmd(self, ensure_term(val)))


class TimezoneRef(ItemRef[str, StrValue], TimezoneType):
    """PV storage ref for timezone values. Stores as str (offset)."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for timezone values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> TimezoneValue:
        """Get the timezone value."""

        def parse_timezone(s: str) -> timezone:
            if s == "UTC":
                from datetime import UTC

                return UTC
            sign = 1 if s[0] == "+" else -1
            parts = s[1:].split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

        return TimezoneValue(FuncCallOp(parse_timezone, self))

    def set(self, value: timezone | str | TimezoneType) -> TimezoneValue:
        """Set the timezone value."""
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
        return TimezoneValue(ItemSetCmd(self, ensure_term(val)))


# =============================================================================
# PATH AND UUID PV REFS
# =============================================================================


class PathRef(ItemRef[str, StrValue], PathType):
    """PV storage ref for Path values. Stores as str."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for Path values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> PathValue:
        """Get the Path value."""
        return PathValue.from_str(self)

    def set(self, value: Path | str | PathType) -> PathValue:
        """Set the Path value."""
        if isinstance(value, Path):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return PathValue(ItemSetCmd(self, ensure_term(val)))


class UUIDRef(ItemRef[str, StrValue], UUIDType):
    """PV storage ref for UUID values. Stores as str."""

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrValue,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for UUID values."""
        return Slot(cls)  # type: ignore[return-value]

    def get(self) -> UUIDValue:
        """Get the UUID value."""
        return UUIDValue.from_str(self)

    def set(self, value: UUID | str | UUIDType) -> UUIDValue:
        """Set the UUID value."""
        if isinstance(value, UUID):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return UUIDValue(ItemSetCmd(self, ensure_term(val)))
