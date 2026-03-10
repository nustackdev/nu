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
from typing import TYPE_CHECKING

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
from everybase import Arg, Term
from everybase.abc import (
    FuncCallOp,
    MethodCallOp,
    ToFloatOp,
    ToIntOp,
    ToStrOp,
    ensure_term,
)
from everybase.shape import Slot
from everybase.shape.morphisms.item import ItemStoreCmd

from .base import RefBase


if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import Path
    from uuid import UUID

    from everybase.shape import Shape


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
    def slot(cls) -> DecimalRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return DecimalValue.from_str(op)

    def store(self, value: Arg[Decimal | str]) -> DecimalValue:
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return DecimalValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> FractionRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return FractionValue.from_str(op)

    def store(self, value: Arg[Fraction | str]) -> FractionValue:
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return FractionValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> ComplexRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexValue(FuncCallOp(parse_complex, op))

    def store(self, value: Arg[complex | str]) -> ComplexValue:
        # complex uses custom "real,imag" format — str(complex) gives "(1+2j)"
        if isinstance(value, Term):

            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCallOp(format_complex, value)
        elif isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        else:
            val = str(value)
        return ComplexValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> BasisPointRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return BasisPointValue.from_int(op)

    def store(self, value: Arg[BasisPoint | int]) -> BasisPointValue:
        if isinstance(value, Term):
            val = ToIntOp(value)
        else:
            val = int(value)
        return BasisPointValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> PercentageRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return PercentageValue.from_float(op)

    def store(self, value: Arg[Percentage | float]) -> PercentageValue:
        if isinstance(value, Term):
            val = ToFloatOp(value)
        else:
            val = float(value)
        return PercentageValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> DateRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return DateValue.from_iso(op)

    def store(self, value: Arg[date | str]) -> DateValue:
        """Stores as ISO string."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return DateValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> DatetimeRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return DatetimeValue.from_iso(op)

    def store(self, value: Arg[datetime | str]) -> DatetimeValue:
        """Stores as ISO string."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return DatetimeValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> TimeRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return TimeValue.from_iso(op)

    def store(self, value: Arg[time | str]) -> TimeValue:
        """Stores as ISO string."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return TimeValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> TimedeltaRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return TimedeltaValue.from_seconds(op)

    def store(self, value: Arg[timedelta | float]) -> TimedeltaValue:
        """Stores as float (total seconds)."""
        if isinstance(value, Term):
            # timedelta is stdlib — no __float__, so use .total_seconds()
            val = MethodCallOp(value, "total_seconds")
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return TimedeltaValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> TimezoneRef:
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

    def store(self, value: Arg[timezone | str]) -> TimezoneValue:
        # timezone uses custom offset format — no standard dunder
        if isinstance(value, Term):

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
        elif isinstance(value, timezone):
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
        else:
            val = str(value)
        return TimezoneValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> PathRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return PathValue.from_str(op)

    def store(self, value: Arg[Path | str]) -> PathValue:
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return PathValue(ItemStoreCmd(self, ensure_term(val)))


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
    def slot(cls) -> UUIDRef:
        return Slot(cls)  # type: ignore[return-value]

    def result(self, op: Term) -> object:
        return UUIDValue.from_str(op)

    def store(self, value: Arg[UUID | str]) -> UUIDValue:
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return UUIDValue(ItemStoreCmd(self, ensure_term(val)))
