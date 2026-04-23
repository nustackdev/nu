"""PV storage refs for standard library types.

These refs store values in PV storage with serialization/deserialization.
Pattern: PV*Ref = ItemRef[StorageType, StrI] + *Type + load/store methods

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
from typing import TYPE_CHECKING, ClassVar

from nu import (
    Arg,
    FloatI,
    FuncCall,
    IntI,
    MethodCall,
    NoneI,
    Nu,
    StrI,
    ToFloat,
    ToInt,
    ToStr,
    ensure_nu,
)
from nu.shapes import Slot
from nu.terms import Mode
from nu.shapes.ops import ItemStoreCmd
from nu.stdlib import BasisPoint, Percentage
from nu.stdlib.cmath import ComplexI, _ComplexI
from nu.stdlib.datetime import (
    DateI,
    DatetimeI,
    TimedeltaI,
    TimeI,
    TimezoneI,
    _DateI,
    _DatetimeI,
    _TimedeltaI,
    _TimeI,
    _TimezoneI,
)
from nu.stdlib.decimal import DecimalI, _DecimalI
from nu.stdlib.fin import BasisPointI, PercentageI, _BasisPointI, _PercentageI
from nu.stdlib.fractions import FractionI, _FractionI
from nu.stdlib.pathlib import PathI, _PathI
from nu.stdlib.uuid import _UUIDI, UUIDI

from .items import ItemRef


if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import Path
    from typing import Self
    from uuid import UUID

    from nu.shapes import Shape
    from virtuals.loc import path

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


class DecimalRef(ItemRef[str, StrI], _DecimalI):
    """PV storage ref for Decimal values. Stores as str."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return DecimalI.from_str(op)

    def store(self, value: Arg[Decimal | str]) -> NoneI:
        """Store the Decimal value."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class FractionRef(ItemRef[str, StrI], _FractionI):
    """PV storage ref for Fraction values. Stores as str."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return FractionI.from_str(op)

    def store(self, value: Arg[Fraction | str]) -> NoneI:
        """Store the Fraction value."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class ComplexRef(ItemRef[str, StrI], _ComplexI):
    """PV storage ref for complex values. Stores as str ("real,imag")."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexI(FuncCall(parse_complex, op))

    def store(self, value: Arg[complex | str]) -> NoneI:
        """Store the complex value."""
        if isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        elif isinstance(value, str):
            val = value
        else:

            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCall(format_complex, value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class BasisPointRef(ItemRef[int, IntI], _BasisPointI):
    """PV storage ref for BasisPoint values. Stores as int."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=int,
            value_value_type=IntI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for BasisPoint values."""
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> BasisPoint:  # noqa: D102
        return BasisPoint(int(raw)) if not isinstance(raw, BasisPoint) else raw

    def result(self, op: Nu) -> object:  # noqa: D102
        return BasisPointI.from_int(op)

    def store(self, value: Arg[BasisPoint | int]) -> NoneI:
        """Store the BasisPoint value."""
        if isinstance(value, Nu):
            val = ToInt(value)
        else:
            val = int(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class PercentageRef(ItemRef[float, FloatI], _PercentageI):
    """PV storage ref for Percentage values. Stores as float."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatI,
            parent=parent,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for Percentage values."""
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> Percentage:  # noqa: D102
        return Percentage(float(raw)) if not isinstance(raw, Percentage) else raw

    def result(self, op: Nu) -> object:  # noqa: D102
        return PercentageI.from_float(op)

    def store(self, value: Arg[Percentage | float]) -> NoneI:
        """Store the Percentage value."""
        if isinstance(value, Nu):
            val = ToFloat(value)
        else:
            val = float(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


# =============================================================================
# DATETIME PV REFS
# =============================================================================


class DateRef(ItemRef[str, StrI], _DateI):
    """PV storage ref for date values. Stores as str (ISO format)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return DateI.from_iso(op)

    def store(self, value: Arg[date | str]) -> NoneI:
        """Store the date value. Stores as ISO string."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class DatetimeRef(ItemRef[str, StrI], _DatetimeI):
    """PV storage ref for datetime values. Stores as str (ISO format)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return DatetimeI.from_iso(op)

    def store(self, value: Arg[datetime | str]) -> NoneI:
        """Store the datetime value. Stores as ISO string."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class TimeRef(ItemRef[str, StrI], _TimeI):
    """PV storage ref for time values. Stores as str (ISO format)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return TimeI.from_iso(op)

    def store(self, value: Arg[time | str]) -> NoneI:
        """Store the time value. Stores as ISO string."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class TimedeltaRef(ItemRef[float, FloatI], _TimedeltaI):
    """PV storage ref for timedelta values. Stores as float (seconds)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=float,
            value_value_type=FloatI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return TimedeltaI.from_seconds(op)

    def store(self, value: Arg[timedelta | float]) -> NoneI:
        """Store the timedelta value. Stores as float (seconds)."""
        if isinstance(value, Nu):
            # timedelta is stdlib — no __float__, so use .total_seconds()
            val = MethodCall(value, "total_seconds")
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class TimezoneRef(ItemRef[str, StrI], _TimezoneI):
    """PV storage ref for timezone values. Stores as str (offset)."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        def parse_timezone(s: str) -> timezone:
            if s == "UTC":
                from datetime import UTC

                return UTC
            sign = 1 if s[0] == "+" else -1
            parts = s[1:].split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

        return TimezoneI(FuncCall(parse_timezone, op))

    def store(self, value: Arg[timezone | str]) -> NoneI:
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

            val = FuncCall(format_timezone, value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


# =============================================================================
# PATH AND UUID PV REFS
# =============================================================================


class PathRef(ItemRef[str, StrI], _PathI):
    """PV storage ref for Path values. Stores as str."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return PathI.from_str(op)

    def store(self, value: Arg[Path | str]) -> NoneI:
        """Store the Path value."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))


class UUIDRef(ItemRef[str, StrI], _UUIDI):
    """PV storage ref for UUID values. Stores as str."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address=address,
            value_type=str,
            value_value_type=StrI,
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

    def result(self, op: Nu) -> object:  # noqa: D102
        return UUIDI.from_str(op)

    def store(self, value: Arg[UUID | str]) -> NoneI:
        """Store the UUID value."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return NoneI(ItemStoreCmd(self, ensure_nu(val)))
