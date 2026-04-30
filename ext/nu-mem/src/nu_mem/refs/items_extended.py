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

from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING, ClassVar

from nu import (
    Arg,
    FuncCall,
    MethodCall,
    NoneForm,
    Nu,
    ToFloat,
    ToInt,
    ToStr,
)
from nu.shapes import Slot
from nu.shapes.commands.item import ItemStoreCmd
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
from nu.terms import Mode

from .base import RefBase


if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import Path
    from uuid import UUID

    from nu.shapes import Shape


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


class DecimalRef(RefBase[str], _DecimalI):
    """Dict storage ref for Decimal values. Stores as str."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> DecimalRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> Decimal:
        from decimal import Decimal as DecimalCls

        return DecimalCls(raw) if not isinstance(raw, DecimalCls) else raw

    def result(self, op: Nu) -> object:
        return DecimalI.from_str(op)

    def store(self, value: Arg[Decimal | str]) -> NoneForm:
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return NoneForm(ItemStoreCmd(self, val))


class FractionRef(RefBase[str], _FractionI):
    """Dict storage ref for Fraction values. Stores as str."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> FractionRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> Fraction:
        from fractions import Fraction as FractionCls

        return FractionCls(raw) if not isinstance(raw, FractionCls) else raw

    def result(self, op: Nu) -> object:
        return FractionI.from_str(op)

    def store(self, value: Arg[Fraction | str]) -> NoneForm:
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return NoneForm(ItemStoreCmd(self, val))


class ComplexRef(RefBase[str], _ComplexI):
    """Dict storage ref for complex values. Stores as str ("real,imag")."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> ComplexRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> complex:
        if isinstance(raw, complex):
            return raw
        parts = str(raw).split(",")
        return complex(float(parts[0]), float(parts[1]))

    def result(self, op: Nu) -> object:
        def parse_complex(s: str) -> complex:
            parts = s.split(",")
            return complex(float(parts[0]), float(parts[1]))

        return ComplexI(FuncCall(parse_complex, op))

    def store(self, value: Arg[complex | str]) -> NoneForm:
        # complex uses custom "real,imag" format — str(complex) gives "(1+2j)"
        if isinstance(value, Nu):

            def format_complex(c: complex) -> str:
                return f"{c.real},{c.imag}"

            val = FuncCall(format_complex, value)
        elif isinstance(value, complex):
            val = f"{value.real},{value.imag}"
        else:
            val = str(value)
        return NoneForm(ItemStoreCmd(self, val))


class BasisPointRef(RefBase[int], _BasisPointI):
    """Dict storage ref for BasisPoint values. Stores as int."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> BasisPointRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> BasisPoint:
        return BasisPoint(int(raw)) if not isinstance(raw, BasisPoint) else raw

    def result(self, op: Nu) -> object:
        return BasisPointI.from_int(op)

    def store(self, value: Arg[BasisPoint | int]) -> NoneForm:
        if isinstance(value, Nu):
            val = ToInt(value)
        else:
            val = int(value)
        return NoneForm(ItemStoreCmd(self, val))


class PercentageRef(RefBase[float], _PercentageI):
    """Dict storage ref for Percentage values. Stores as float."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> PercentageRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> Percentage:
        return Percentage(float(raw)) if not isinstance(raw, Percentage) else raw

    def result(self, op: Nu) -> object:
        return PercentageI.from_float(op)

    def store(self, value: Arg[Percentage | float]) -> NoneForm:
        if isinstance(value, Nu):
            val = ToFloat(value)
        else:
            val = float(value)
        return NoneForm(ItemStoreCmd(self, val))


# =============================================================================
# DATETIME DICT REFS
# =============================================================================


class DateRef(RefBase[str], _DateI):
    """Dict storage ref for date values. Stores as str (ISO format)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> DateRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> date:
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw))

    def result(self, op: Nu) -> object:
        return DateI.from_iso(op)

    def store(self, value: Arg[date | str]) -> NoneForm:
        """Stores as ISO string."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return NoneForm(ItemStoreCmd(self, val))


class DatetimeRef(RefBase[str], _DatetimeI):
    """Dict storage ref for datetime values. Stores as str (ISO format)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> DatetimeRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> datetime:
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=UTC)
        return datetime.fromisoformat(str(raw))

    def result(self, op: Nu) -> object:
        return DatetimeI.from_iso(op)

    def store(self, value: Arg[datetime | str]) -> DatetimeI:
        """Stores as ISO string."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return DatetimeI(ItemStoreCmd(self, val))


class TimeRef(RefBase[str], _TimeI):
    """Dict storage ref for time values. Stores as str (ISO format)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> TimeRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> time:
        if isinstance(raw, time):
            return raw
        return time.fromisoformat(str(raw))

    def result(self, op: Nu) -> object:
        return TimeI.from_iso(op)

    def store(self, value: Arg[time | str]) -> TimeI:
        """Stores as ISO string."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return TimeI(ItemStoreCmd(self, val))


class TimedeltaRef(RefBase[float], _TimedeltaI):
    """Dict storage ref for timedelta values. Stores as float (seconds)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> TimedeltaRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> timedelta:
        if isinstance(raw, timedelta):
            return raw
        return timedelta(seconds=float(raw))

    def result(self, op: Nu) -> object:
        return TimedeltaI.from_seconds(op)

    def store(self, value: Arg[timedelta | float]) -> TimedeltaI:
        """Stores as float (total seconds)."""
        if isinstance(value, Nu):
            # timedelta is stdlib — no __float__, so use .total_seconds()
            val = MethodCall(value, "total_seconds")
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return TimedeltaI(ItemStoreCmd(self, val))


class TimezoneRef(RefBase[str], _TimezoneI):
    """Dict storage ref for timezone values. Stores as str (offset)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> TimezoneRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> timezone:
        if isinstance(raw, timezone):
            return raw
        s = str(raw)
        if s == "UTC":
            from datetime import UTC

            return UTC  # type: ignore[return-value]
        sign = 1 if s[0] == "+" else -1
        parts = s[1:].split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

    def result(self, op: Nu) -> object:
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

    def store(self, value: Arg[timezone | str]) -> TimezoneI:
        # timezone uses custom offset format — no standard dunder
        if isinstance(value, Nu):

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
        return TimezoneI(ItemStoreCmd(self, val))


# =============================================================================
# PATH AND UUID DICT REFS
# =============================================================================


class PathRef(RefBase[str], _PathI):
    """Dict storage ref for Path values. Stores as str."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> PathRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> Path:
        from pathlib import PurePath

        return PurePath(raw) if not isinstance(raw, PurePath) else raw

    def result(self, op: Nu) -> object:
        return PathI.from_str(op)

    def store(self, value: Arg[Path | str]) -> PathI:
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return PathI(ItemStoreCmd(self, val))


class UUIDRef(RefBase[str], _UUIDI):
    """Dict storage ref for UUID values. Stores as str."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(
        self,
        *,
        address: str | Nu,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address=address, parent=parent, owner_shape=owner_shape)

    @classmethod
    def slot(cls) -> UUIDRef:
        return Slot(cls)  # type: ignore[return-value]

    def coerce(self, raw: object) -> UUID:
        import uuid

        return uuid.UUID(raw) if not isinstance(raw, uuid.UUID) else raw

    def result(self, op: Nu) -> object:
        return UUIDI.from_str(op)

    def store(self, value: Arg[UUID | str]) -> UUIDI:
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = str(value)
        return UUIDI(ItemStoreCmd(self, val))
