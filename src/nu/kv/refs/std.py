"""virtuals-substrate refs for standard-library value types.

Each ref is a typed leaf on the virtuals View substrate whose stored form differs
from its domain type, so it overrides ``store`` (domain -> storage) and
``coerce`` (storage -> domain). The value interface comes from mixing in the
matching ``nu.std`` Form, exactly as ``IntRef`` mixes in ``Int``.

Storage formats:
- Decimal / Fraction / complex / Path / UUID: ``str``
- date / datetime / time / timezone: ``str`` (ISO / offset)
- BasisPoint: ``int`` (raw basis points)
- Percentage: ``float`` (raw percentage)
- timedelta: ``float`` (total seconds)
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.core import ToFloat, ToInt, ToStr
from nu.domains.shape import SetCmd, Slot
from nu.forms import Float, Int, Str
from nu.lang import Nu
from nu.std.cmath import complex as ComplexForm
from nu.std.datetime import date as DateForm
from nu.std.datetime import datetime as DatetimeForm
from nu.std.datetime import time as TimeForm
from nu.std.datetime import timedelta as TimedeltaForm
from nu.std.datetime import timezone as TimezoneForm
from nu.std.datetime.interactions import TimedeltaTotalSeconds
from nu.std.decimal import Decimal as DecimalForm
from nu.std.fin import BasisPoint as BasisPointForm
from nu.std.fin import Percentage as PercentageForm
from nu.std.fin import PyBasisPoint, PyPercentage
from nu.std.fractions import Fraction as FractionForm
from nu.std.pathlib import Path as PathForm
from nu.std.uuid import UUID as UUIDForm

from .items import ItemRef


UTC = timezone.utc


if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction
    from pathlib import PurePath
    from uuid import UUID

    from nu.domains.shape import Shape
    from nu.lang import Arg

    from .base import PrimitiveRef


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


def _parse_timezone(raw: str) -> timezone:
    """Parse ``str(timezone)`` output (``"UTC"`` or ``"UTC+05:30"``)."""
    s = raw[3:] if raw.startswith("UTC") else raw
    if not s:
        return UTC
    sign = 1 if s[0] == "+" else -1
    parts = s[1:].split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))


# =============================================================================
# NUMERIC REFS
# =============================================================================


class DecimalRef(ItemRef, DecimalForm):
    """virtuals Decimal ref. Stores as str (exact representation)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a Decimal value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> Decimal:
        """Parse the stored str back to a Decimal."""
        from decimal import Decimal as DecimalCls

        return raw if isinstance(raw, DecimalCls) else DecimalCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Decimal | str]) -> SetCmd:
        """Serialize the Decimal to str, then write it."""
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class FractionRef(ItemRef, FractionForm):
    """virtuals Fraction ref. Stores as str (``"numerator/denominator"``)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a Fraction value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> Fraction:
        """Parse the stored str back to a Fraction."""
        from fractions import Fraction as FractionCls

        return raw if isinstance(raw, FractionCls) else FractionCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Fraction | str]) -> SetCmd:
        """Serialize the Fraction to str, then write it."""
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class ComplexRef(ItemRef, ComplexForm):
    """virtuals complex ref. Stores as str (``str(complex)``, round-trips)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a complex value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> complex:
        """Parse the stored str back to a complex."""
        return raw if isinstance(raw, complex) else complex(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[complex | str]) -> SetCmd:
        """Serialize the complex to str, then write it."""
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class BasisPointRef(ItemRef, BasisPointForm):
    """virtuals BasisPoint ref. Stores as int (raw basis points)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=int,
            value_value_type=Int,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a BasisPoint value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> PyBasisPoint:
        """Wrap the stored int back as a BasisPoint."""
        return raw if isinstance(raw, PyBasisPoint) else PyBasisPoint(int(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyBasisPoint | int]) -> SetCmd:
        """Serialize the BasisPoint to int, then write it."""
        val = ToInt(value) if isinstance(value, Nu) else int(value)
        return SetCmd(self, val)


class PercentageRef(ItemRef, PercentageForm):
    """virtuals Percentage ref. Stores as float (raw percentage)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=float,
            value_value_type=Float,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a Percentage value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> PyPercentage:
        """Wrap the stored float back as a Percentage."""
        return raw if isinstance(raw, PyPercentage) else PyPercentage(float(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyPercentage | float]) -> SetCmd:
        """Serialize the Percentage to float, then write it."""
        val = ToFloat(value) if isinstance(value, Nu) else float(value)
        return SetCmd(self, val)


# =============================================================================
# DATETIME REFS
# =============================================================================


class DateRef(ItemRef, DateForm):
    """virtuals date ref. Stores as ISO str."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a date value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> date:
        """Parse the stored ISO str back to a date."""
        return raw if isinstance(raw, date) else date.fromisoformat(str(raw))

    def set(self, value: Arg[date | str]) -> SetCmd:
        """Serialize the date to an ISO str, then write it."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return SetCmd(self, val)


class DatetimeRef(ItemRef, DatetimeForm):
    """virtuals datetime ref. Stores as ISO str."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a datetime value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> datetime:
        """Parse the stored ISO str (or epoch) back to a datetime."""
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=UTC)
        return datetime.fromisoformat(str(raw))

    def set(self, value: Arg[datetime | str]) -> SetCmd:
        """Serialize the datetime to an ISO str, then write it."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return SetCmd(self, val)


class TimeRef(ItemRef, TimeForm):
    """virtuals time ref. Stores as ISO str."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a time value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> time:
        """Parse the stored ISO str back to a time."""
        return raw if isinstance(raw, time) else time.fromisoformat(str(raw))

    def set(self, value: Arg[time | str]) -> SetCmd:
        """Serialize the time to an ISO str, then write it."""
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return SetCmd(self, val)


class TimedeltaRef(ItemRef, TimedeltaForm):
    """virtuals timedelta ref. Stores as float (total seconds)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=float,
            value_value_type=Float,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a timedelta value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> timedelta:
        """Rebuild the timedelta from the stored total-seconds float."""
        return raw if isinstance(raw, timedelta) else timedelta(seconds=float(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[timedelta | float]) -> SetCmd:
        """Serialize the timedelta to total-seconds float, then write it."""
        if isinstance(value, Nu):
            val = TimedeltaTotalSeconds(value)
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return SetCmd(self, val)


class TimezoneRef(ItemRef, TimezoneForm):
    """virtuals timezone ref. Stores as str (``str(timezone)`` offset)."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a timezone value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> timezone:
        """Parse the stored offset str back to a timezone."""
        return raw if isinstance(raw, timezone) else _parse_timezone(str(raw))

    def set(self, value: Arg[timezone | str]) -> SetCmd:
        """Serialize the timezone to its offset str, then write it."""
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


# =============================================================================
# PATH AND UUID REFS
# =============================================================================


class PathRef(ItemRef, PathForm):
    """virtuals Path ref. Stores as str."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a Path value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> PurePath:
        """Parse the stored str back to a PurePath."""
        from pathlib import PurePath

        return raw if isinstance(raw, PurePath) else PurePath(str(raw))

    def set(self, value: Arg[PurePath | str]) -> SetCmd:
        """Serialize the Path to str, then write it."""
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class UUIDRef(ItemRef, UUIDForm):
    """virtuals UUID ref. Stores as str."""

    def __init__(
        self,
        address: str | int | Nu,
        *,
        parent_ref: PrimitiveRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            value_type=str,
            value_value_type=Str,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(cls) -> Self:  # type: ignore[override]
        """Declare a slot holding a UUID value."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> UUID:
        """Parse the stored str back to a UUID."""
        import uuid

        return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))

    def set(self, value: Arg[UUID | str]) -> SetCmd:
        """Serialize the UUID to str, then write it."""
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
