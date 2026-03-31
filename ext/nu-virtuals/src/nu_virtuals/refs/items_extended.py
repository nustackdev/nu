"""PV storage refs for standard library types.

These refs store values in PV storage with serialization/deserialization.
Pattern: PV*Ref = ItemRef[StorageType, StrValue] + *Type + load/store methods

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

from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING

from nu_datetime import (
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
from nu_fin import (
    BasisPoint,
    BasisPointType,
    BasisPointValue,
    Percentage,
    PercentageType,
    PercentageValue,
)
from nu_math import (
    ComplexType,
    ComplexValue,
    DecimalType,
    DecimalValue,
    FractionType,
    FractionValue,
)
from nu_path import PathType, PathValue
from nu_uuid import UUIDType, UUIDValue
from nu import Arg, Term
from nu.abc import (
    FloatValue,
    FuncCallOp,
    IntValue,
    MethodCallOp,
    NoneValue,
    StrValue,
    ToFloatOp,
    ToIntOp,
    ToStrOp,
    ensure_term,
)
from nu.shape import Slot
from nu.shape.morphisms import ItemStoreCmd

from .items import ItemRef


if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import Path
    from typing import Self
    from uuid import UUID

    from virtuals.loc import path

    from nu.shape import Shape

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

    def coerce(self, raw: object) -> Decimal:  # noqa: D102
        from decimal import Decimal as DecimalCls

        return DecimalCls(raw) if not isinstance(raw, DecimalCls) else raw

    def result(self, op: Term) -> object:  # noqa: D102
        return DecimalValue.from_str(op)

    def store(self, value: Arg[Decimal | str]) -> NoneValue:
        """Store the Decimal value."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> Fraction:  # noqa: D102
        from fractions import Fraction as FractionCls

        return FractionCls(raw) if not isinstance(raw, FractionCls) else raw

    def result(self, op: Term) -> object:  # noqa: D102
        return FractionValue.from_str(op)

    def store(self, value: Arg[Fraction | str]) -> NoneValue:
        """Store the Fraction value."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> complex:  # noqa: D102
        if isinstance(raw, complex):
            return raw
        parts = str(raw).split(",")
        return complex(float(parts[0]), float(parts[1]))

    def result(self, op: Term) -> object:  # noqa: D102
        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexValue(FuncCallOp(parse_complex, op))

    def store(self, value: Arg[complex | str]) -> NoneValue:
        """Store the complex value."""
        if isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        elif isinstance(value, str):
            val = value
        else:

            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCallOp(format_complex, value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> BasisPoint:  # noqa: D102
        return BasisPoint(int(raw)) if not isinstance(raw, BasisPoint) else raw

    def result(self, op: Term) -> object:  # noqa: D102
        return BasisPointValue.from_int(op)

    def store(self, value: Arg[BasisPoint | int]) -> NoneValue:
        """Store the BasisPoint value."""
        if isinstance(value, Term):
            val = ToIntOp(value)
        else:
            val = int(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> Percentage:  # noqa: D102
        return Percentage(float(raw)) if not isinstance(raw, Percentage) else raw

    def result(self, op: Term) -> object:  # noqa: D102
        return PercentageValue.from_float(op)

    def store(self, value: Arg[Percentage | float]) -> NoneValue:
        """Store the Percentage value."""
        if isinstance(value, Term):
            val = ToFloatOp(value)
        else:
            val = float(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> date:  # noqa: D102
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw))

    def result(self, op: Term) -> object:  # noqa: D102
        return DateValue.from_iso(op)

    def store(self, value: Arg[date | str]) -> NoneValue:
        """Store the date value. Stores as ISO string."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> datetime:  # noqa: D102
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=UTC)
        return datetime.fromisoformat(str(raw))

    def result(self, op: Term) -> object:  # noqa: D102
        return DatetimeValue.from_iso(op)

    def store(self, value: Arg[datetime | str]) -> NoneValue:
        """Store the datetime value. Stores as ISO string."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> time:  # noqa: D102
        if isinstance(raw, time):
            return raw
        return time.fromisoformat(str(raw))

    def result(self, op: Term) -> object:  # noqa: D102
        return TimeValue.from_iso(op)

    def store(self, value: Arg[time | str]) -> NoneValue:
        """Store the time value. Stores as ISO string."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> timedelta:  # noqa: D102
        if isinstance(raw, timedelta):
            return raw
        return timedelta(seconds=float(raw))

    def result(self, op: Term) -> object:  # noqa: D102
        return TimedeltaValue.from_seconds(op)

    def store(self, value: Arg[timedelta | float]) -> NoneValue:
        """Store the timedelta value. Stores as float (seconds)."""
        if isinstance(value, Term):
            # timedelta is stdlib — no __float__, so use .total_seconds()
            val = MethodCallOp(value, "total_seconds")
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> timezone:  # noqa: D102
        if isinstance(raw, timezone):
            return raw
        s = str(raw)
        if s == "UTC":
            from datetime import UTC

            return UTC
        sign = 1 if s[0] == "+" else -1
        parts = s[1:].split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

    def result(self, op: Term) -> object:  # noqa: D102
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

    def store(self, value: Arg[timezone | str]) -> NoneValue:
        """Store the timezone value."""
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
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> Path:  # noqa: D102
        from pathlib import PurePath

        return PurePath(raw) if not isinstance(raw, PurePath) else raw

    def result(self, op: Term) -> object:  # noqa: D102
        return PathValue.from_str(op)

    def store(self, value: Arg[Path | str]) -> NoneValue:
        """Store the Path value."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))


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

    def coerce(self, raw: object) -> UUID:  # noqa: D102
        import uuid

        return uuid.UUID(raw) if not isinstance(raw, uuid.UUID) else raw

    def result(self, op: Term) -> object:  # noqa: D102
        return UUIDValue.from_str(op)

    def store(self, value: Arg[UUID | str]) -> NoneValue:
        """Store the UUID value."""
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return NoneValue(ItemStoreCmd(self, ensure_term(val)))
