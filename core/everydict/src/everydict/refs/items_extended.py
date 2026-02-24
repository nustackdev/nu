# ruff: noqa: D102
"""Dict storage refs for standard library types.

These refs store values in nested Python dicts with serialization/deserialization.

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
from typing import TYPE_CHECKING, Self
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
from everybase.abc import FuncCallOp, MethodCallOp, ensure_term
from everyshape import Slot
from everyshape.morphisms.item import ItemSetCmd

from .base import RefBase


if TYPE_CHECKING:
    from everybase import Term
    from everyshape import Shape


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
# NUMERIC DICT REFS
# =============================================================================


class DecimalRef(RefBase[str], DecimalType):
    """Dict storage ref for Decimal values. Stores as str."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return DecimalValue.from_str(op)

    def set(self, value: Decimal | str | DecimalType) -> DecimalValue:
        if isinstance(value, Decimal):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return DecimalValue(ItemSetCmd(self, ensure_term(val)))


class FractionRef(RefBase[str], FractionType):
    """Dict storage ref for Fraction values. Stores as str."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return FractionValue.from_str(op)

    def set(self, value: Fraction | str | FractionType) -> FractionValue:
        if isinstance(value, Fraction):
            val = f"{value.numerator}/{value.denominator}"
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return FractionValue(ItemSetCmd(self, ensure_term(val)))


class ComplexRef(RefBase[str], ComplexType):
    """Dict storage ref for complex values. Stores as str ("real,imag")."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexValue(FuncCallOp(parse_complex, op))

    def set(self, value: complex | str | ComplexType) -> ComplexValue:
        if isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        elif isinstance(value, str):
            val = value
        else:

            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCallOp(format_complex, value)
        return ComplexValue(ItemSetCmd(self, ensure_term(val)))


class BasisPointRef(RefBase[int], BasisPointType):
    """Dict storage ref for BasisPoint values. Stores as int."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return BasisPointValue.from_int(op)

    def set(self, value: BasisPoint | int | BasisPointType) -> BasisPointValue:
        if isinstance(value, BasisPoint):
            val = value.value
        elif isinstance(value, int):
            val = value
        else:
            val = MethodCallOp(value, "to_int")
        return BasisPointValue(ItemSetCmd(self, ensure_term(val)))


class PercentageRef(RefBase[float], PercentageType):
    """Dict storage ref for Percentage values. Stores as float."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return PercentageValue.from_float(op)

    def set(self, value: Percentage | float | PercentageType) -> PercentageValue:
        if isinstance(value, Percentage):
            val = value.value
        elif isinstance(value, (int, float)):
            val = float(value)
        else:
            val = MethodCallOp(value, "to_float")
        return PercentageValue(ItemSetCmd(self, ensure_term(val)))


# =============================================================================
# DATETIME DICT REFS
# =============================================================================


class DateRef(RefBase[str], DateType):
    """Dict storage ref for date values. Stores as str (ISO format)."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return DateValue.from_iso(op)

    def set(self, value: date | str | DateType) -> DateValue:
        if isinstance(value, date):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "isoformat")
        return DateValue(ItemSetCmd(self, ensure_term(val)))


class DatetimeRef(RefBase[str], DatetimeType):
    """Dict storage ref for datetime values. Stores as str (ISO format)."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return DatetimeValue.from_iso(op)

    def set(self, value: datetime | str | DatetimeType) -> DatetimeValue:
        if isinstance(value, datetime):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "isoformat")
        return DatetimeValue(ItemSetCmd(self, ensure_term(val)))


class TimeRef(RefBase[str], TimeType):
    """Dict storage ref for time values. Stores as str (ISO format)."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return TimeValue.from_iso(op)

    def set(self, value: time | str | TimeType) -> TimeValue:
        if isinstance(value, time):
            val = value.isoformat()
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "isoformat")
        return TimeValue(ItemSetCmd(self, ensure_term(val)))


class TimedeltaRef(RefBase[float], TimedeltaType):
    """Dict storage ref for timedelta values. Stores as float (seconds)."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return TimedeltaValue.from_seconds(op)

    def set(self, value: timedelta | float | TimedeltaType) -> TimedeltaValue:
        if isinstance(value, timedelta):
            val = value.total_seconds()
        elif isinstance(value, (int, float)):
            val = float(value)
        else:
            val = MethodCallOp(value, "total_seconds")
        return TimedeltaValue(ItemSetCmd(self, ensure_term(val)))


class TimezoneRef(RefBase[str], TimezoneType):
    """Dict storage ref for timezone values. Stores as str (offset)."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        def parse_timezone(s: str) -> timezone:
            if s == "UTC":
                from datetime import UTC

                return UTC
            sign = 1 if s[0] == "+" else -1
            parts = s[1:].split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

        return TimezoneValue(FuncCallOp(parse_timezone, op))

    def set(self, value: timezone | str | TimezoneType) -> TimezoneValue:
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
# PATH AND UUID DICT REFS
# =============================================================================


class PathRef(RefBase[str], PathType):
    """Dict storage ref for Path values. Stores as str."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return PathValue.from_str(op)

    def set(self, value: Path | str | PathType) -> PathValue:
        if isinstance(value, Path):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return PathValue(ItemSetCmd(self, ensure_term(val)))


class UUIDRef(RefBase[str], UUIDType):
    """Dict storage ref for UUID values. Stores as str."""

    def __init__(
        self,
        *,
        address: str | Term,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return UUIDValue.from_str(op)

    def set(self, value: UUID | str | UUIDType) -> UUIDValue:
        if isinstance(value, UUID):
            val = str(value)
        elif isinstance(value, str):
            val = value
        else:
            val = MethodCallOp(value, "__str__")
        return UUIDValue(ItemSetCmd(self, ensure_term(val)))
