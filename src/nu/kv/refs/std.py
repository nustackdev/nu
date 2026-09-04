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
    from nu.lang import Arg, IntArg, StrArg

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
    """A Decimal leaf in KV storage, kept exact by storing its str form.

    Notes:
        - Stored as str, so the value round-trips digit for digit; that is
          the whole reason to pick this over FloatRef for money.
        - Reads parse back to a Decimal, so the arithmetic on the ref is
          decimal arithmetic, not float arithmetic.
        - An absent leaf reads as EMPTY, not as zero.

    Example:
        class Order(Shape):
            price = DecimalRef.slot()
        run(Order.price.set(Decimal("19.99")), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a Decimal to the leaf, serialized to its str form.

        Args:
            value: a Decimal, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr so the conversion happens at run time.
            - The str is whatever ``str()`` gives, so it parses back exactly.

        Example:
            run(Order.price.set(Decimal("19.99")), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class FractionRef(ItemRef, FractionForm):
    """A Fraction leaf in KV storage, stored as its ``numerator/denominator`` str.

    Notes:
        - Stored as str, so the ratio survives exactly instead of being
          flattened to a float.
        - Reads parse back to a Fraction, already in lowest terms because
          that is what Fraction does with the str.
        - An absent leaf reads as EMPTY.

    Example:
        class Split(Shape):
            share = FractionRef.slot()
        run(Split.share.set(Fraction(1, 3)), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a Fraction to the leaf, serialized to its str form.

        Args:
            value: a Fraction, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr so the conversion happens at run time.

        Example:
            run(Split.share.set(Fraction(1, 3)), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class ComplexRef(ItemRef, ComplexForm):
    """A complex leaf in KV storage, stored as the str Python prints for it.

    Notes:
        - Stored as str because a KV leaf holds one scalar; the pair is kept
          in the one text rather than in two slots.
        - Reads parse back to a complex, so ``real``, ``imag`` and the
          arithmetic all work on the value.
        - An absent leaf reads as EMPTY.

    Example:
        class Wave(Shape):
            amplitude = ComplexRef.slot()
        run(Wave.amplitude.set(complex(1, 2)), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a complex to the leaf, serialized to its str form.

        Args:
            value: a complex, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr so the conversion happens at run time.

        Example:
            run(Wave.amplitude.set(complex(1, 2)), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class BasisPointRef(ItemRef, BasisPointForm):
    """A BasisPoint leaf in KV storage, stored as the raw int count of bps.

    Notes:
        - Stored as an int, so a rate is exact and no float rounding creeps
          in between writes and reads.
        - Reads wrap the int back into a BasisPoint, so the conversions
          (``to_pct``, ``to_dec``) and the fee helpers are there on the ref.
        - An absent leaf reads as EMPTY, not as zero bps.

    Example:
        class Fee(Shape):
            taker = BasisPointRef.slot()
        run(Fee.taker.set(25), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a BasisPoint to the leaf, serialized to its raw int.

        Args:
            value: a BasisPoint, an int count of bps, or an expression
                yielding either.

        Notes:
            - A plain value goes through ``int()`` before the write; an
              expression is wrapped in a ToInt. Either way a fractional
              input truncates toward zero rather than rounding.

        Example:
            run(Fee.taker.set(25), ctx)
        """
        val = ToInt(value) if isinstance(value, Nu) else int(value)
        return SetCmd(self, val)


class PercentageRef(ItemRef, PercentageForm):
    """A Percentage leaf in KV storage, stored as the raw float percentage.

    Notes:
        - Stored as the percentage itself, not as a fraction: 12.5 percent
          is 12.5 on disk, not 0.125.
        - Reads wrap the float back into a Percentage, so the conversions
          (``to_dec``, ``to_bps``) and the apply helpers are on the ref.
        - Float storage, so it carries float rounding; BasisPointRef is the
          exact one.

    Example:
        class Fee(Shape):
            slippage = PercentageRef.slot()
        run(Fee.slippage.set(0.5), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a Percentage to the leaf, serialized to its raw float.

        Args:
            value: a Percentage, a raw float percentage, or an expression
                yielding either.

        Notes:
            - A plain value goes through ``float()`` before the write; an
              expression is wrapped in a ToFloat.
            - The number written is the percentage, so pass 12.5 for 12.5
              percent.

        Example:
            run(Fee.slippage.set(0.5), ctx)
        """
        val = ToFloat(value) if isinstance(value, Nu) else float(value)
        return SetCmd(self, val)


# =============================================================================
# DATETIME REFS
# =============================================================================


class DateRef(ItemRef, DateForm):
    """A date leaf in KV storage, stored as an ISO ``YYYY-MM-DD`` str.

    Notes:
        - ISO on disk, so stored dates sort lexicographically in the same
          order they sort chronologically.
        - Reads parse back to a date, so the field accessors and the
          arithmetic work on the value.
        - An absent leaf reads as EMPTY.

    Example:
        class Order(Shape):
            booked = DateRef.slot()
        run(Order.booked.set(date(2026, 1, 31)), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a date to the leaf, serialized to an ISO str.

        Args:
            value: a date, an ISO str, or an expression yielding either.

        Notes:
            - A plain date is written with ``isoformat``; anything else
              plain is stringified, and an expression is wrapped in a ToStr.
            - A datetime passed here is a date subclass, so it writes its
              full ISO form, and reading that leaf back raises. Use
              DatetimeRef for a moment in time.

        Example:
            run(Order.booked.set(date(2026, 1, 31)), ctx)
        """
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return SetCmd(self, val)


class DatetimeRef(ItemRef, DatetimeForm):
    """A datetime leaf in KV storage, stored as an ISO str.

    Notes:
        - ISO on disk, tz offset included when the datetime carries one;
          a naive datetime stays naive through the round trip.
        - A leaf holding a number instead of a str is read as a POSIX
          timestamp and comes back as an aware UTC datetime, which is how a
          slot written by something outside Nu still reads.
        - An absent leaf reads as EMPTY.

    Example:
        class Order(Shape):
            filled_at = DatetimeRef.slot()
        run(Order.filled_at.set(datetime.now(UTC)), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a datetime to the leaf, serialized to an ISO str.

        Args:
            value: a datetime, an ISO str, or an expression yielding either.

        Notes:
            - A plain datetime is written with ``isoformat``; anything else
              plain is stringified, and an expression is wrapped in a ToStr.
            - Nothing is normalized to UTC on the way in, so the offset the
              value carried is the offset stored.

        Example:
            run(Order.filled_at.set(datetime.now(UTC)), ctx)
        """
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return SetCmd(self, val)


class TimeRef(ItemRef, TimeForm):
    """A time-of-day leaf in KV storage, stored as an ISO ``HH:MM:SS`` str.

    Notes:
        - A wall-clock time with no date attached, so nothing about it
          orders across days.
        - Reads parse back to a time, keeping any tz offset the str carried.
        - An absent leaf reads as EMPTY.

    Example:
        class Window(Shape):
            opens = TimeRef.slot()
        run(Window.opens.set(time(9, 30)), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a time to the leaf, serialized to an ISO str.

        Args:
            value: a time, an ISO str, or an expression yielding either.

        Notes:
            - A plain time is written with ``isoformat``; anything else
              plain is stringified, and an expression is wrapped in a ToStr.

        Example:
            run(Window.opens.set(time(9, 30)), ctx)
        """
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return SetCmd(self, val)


class TimedeltaRef(ItemRef, TimedeltaForm):
    """A timedelta leaf in KV storage, stored as a float count of seconds.

    Notes:
        - One number on disk, so stored durations compare and sort as
          numbers without being parsed first.
        - Reads rebuild the timedelta from that count, so ``days``,
          ``seconds`` and the arithmetic are on the value.
        - An absent leaf reads as EMPTY, not as a zero duration.

    Example:
        class Job(Shape):
            timeout = TimedeltaRef.slot()
        run(Job.timeout.set(timedelta(minutes=5)), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a timedelta to the leaf, serialized to total seconds.

        Args:
            value: a timedelta, a float count of seconds, or an expression
                yielding either.

        Notes:
            - A plain timedelta goes through ``total_seconds``; a plain
              number through ``float()``; an expression is wrapped in a
              TimedeltaTotalSeconds, so it must yield a timedelta.

        Example:
            run(Job.timeout.set(timedelta(minutes=5)), ctx)
        """
        if isinstance(value, Nu):
            val = TimedeltaTotalSeconds(value)
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return SetCmd(self, val)


class TimezoneRef(ItemRef, TimezoneForm):
    """A fixed-offset timezone leaf in KV storage, stored as its offset str.

    Notes:
        - Holds a fixed offset only, spelled the way ``str(timezone)``
          spells it: ``UTC`` or ``UTC+05:30``.
        - A named zone is not what this slot stores: writing a ZoneInfo
          stores its name, and reading that leaf back raises.
        - An absent leaf reads as EMPTY.

    Example:
        class Desk(Shape):
            zone = TimezoneRef.slot()
        run(Desk.zone.set(timezone(timedelta(hours=4))), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a timezone to the leaf, serialized to its offset str.

        Args:
            value: a timezone, an offset str, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr.
            - Only the ``UTC`` and ``UTC±HH:MM`` spellings read back, so
              write a fixed-offset timezone here and nothing else.

        Example:
            run(Desk.zone.set(timezone(timedelta(hours=4))), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


# =============================================================================
# PATH AND UUID REFS
# =============================================================================


class PathRef(ItemRef, PathForm):
    """A filesystem path leaf in KV storage, stored as its str form.

    Notes:
        - Reads come back as a PurePath, so the path surface is the pure
          one: parts, parents, suffixes, joins. Nothing here touches a
          filesystem.
        - Stored as written, so a path written on one platform reads back
          with that platform's separators.
        - An absent leaf reads as EMPTY.

    Example:
        class Job(Shape):
            outdir = PathRef.slot()
        run(Job.outdir.set(PurePath("/var/log")), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a path to the leaf, serialized to str.

        Args:
            value: a path, a str, or an expression yielding either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr.

        Example:
            run(Job.outdir.set(PurePath("/var/log")), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class UUIDRef(ItemRef, UUIDForm):
    """A UUID leaf in KV storage, stored as its canonical hyphenated str.

    Notes:
        - Str on disk rather than 16 raw bytes, so the stored value is
          readable in a dump and matches what other systems expect.
        - Reads parse back to a UUID, so ``version``, ``int_`` and ``hex``
          are on the ref.
        - An absent leaf reads as EMPTY.

    Example:
        class Session(Shape):
            token = UUIDRef.slot()
        run(Session.token.set(uuid4()), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        """Write a UUID to the leaf, serialized to str.

        Args:
            value: a UUID, a str spelling one, or an expression yielding
                either.

        Notes:
            - A plain value is stringified before the write; an expression
              is wrapped in a ToStr.
            - Any spelling ``UUID()`` accepts reads back, so a str without
              hyphens still parses; it is stored as given.

        Example:
            run(Session.token.set(uuid4()), ctx)
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
