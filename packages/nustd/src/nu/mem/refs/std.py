"""Dict-substrate refs for standard-library value types.

Each ref is a typed slot in the nested-dict substrate whose stored form differs
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

    from .base import RefBase


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
    """A Decimal slot in the dict substrate, stored as its exact string form.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored string is ``str(Decimal)``, so precision and trailing
          zeros survive the round trip where a float would lose them.
        - A Decimal already sitting in the data dict is read as it is, so a
          dict populated by hand works either way.

    Yields:
        A Decimal, parsed from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> from decimal import Decimal
        >>> class Quote(nu.Shape):
        ...     price = nu.mem.DecimalRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Quote)
        >>> _ = nu.run(Quote.price.set(Decimal("1.250")), ctx)
        >>> data
        {'price': '1.250'}
        >>> nu.run(Quote.price, ctx)[0]
        Decimal('1.250')
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a Decimal slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> Decimal:
        """Parse the stored str back to a Decimal."""
        from decimal import Decimal as DecimalCls

        return raw if isinstance(raw, DecimalCls) else DecimalCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Decimal | str]) -> SetCmd:
        """Write a Decimal into the slot as its string form.

        Notes:
            - A plain Python value is serialised now, at tree-build time; a
              Nu operand gets a ``ToStr`` node instead, serialised when the
              tree runs.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class FractionRef(ItemRef, FractionForm):
    """A Fraction slot in the dict substrate, stored as ``"numerator/denom"``.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored string is ``str(Fraction)``, already in lowest terms,
          so the exact ratio round-trips.

    Yields:
        A Fraction, parsed from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> from fractions import Fraction
        >>> class Split(nu.Shape):
        ...     share = nu.mem.FractionRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Split)
        >>> _ = nu.run(Split.share.set(Fraction(3, 4)), ctx)
        >>> data
        {'share': '3/4'}
        >>> nu.run(Split.share, ctx)[0]
        Fraction(3, 4)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a Fraction slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> Fraction:
        """Parse the stored str back to a Fraction."""
        from fractions import Fraction as FractionCls

        return raw if isinstance(raw, FractionCls) else FractionCls(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[Fraction | str]) -> SetCmd:
        """Write a Fraction into the slot as its string form.

        Notes:
            - A plain Python value is serialised at tree-build time; a Nu
              operand gets a ``ToStr`` node instead.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class ComplexRef(ItemRef, ComplexForm):
    """A complex slot in the dict substrate, stored as ``str(complex)``.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - ``str(complex)`` is what ``complex(str)`` reads back, so the value
          round-trips exactly, parentheses and all.

    Yields:
        A complex, parsed from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> class Signal(nu.Shape):
        ...     amp = nu.mem.ComplexRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Signal)
        >>> _ = nu.run(Signal.amp.set(complex(1, 2)), ctx)
        >>> data
        {'amp': '(1+2j)'}
        >>> nu.run(Signal.amp.real(), ctx)[0]
        1.0
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a complex slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> complex:
        """Parse the stored str back to a complex."""
        return raw if isinstance(raw, complex) else complex(raw)  # type: ignore[arg-type]

    def set(self, value: Arg[complex | str]) -> SetCmd:
        """Write a complex into the slot as its string form.

        Notes:
            - A plain Python value is serialised at tree-build time; a Nu
              operand gets a ``ToStr`` node instead.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class BasisPointRef(ItemRef, BasisPointForm):
    """A BasisPoint slot in the dict substrate, stored as a raw int of bps.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as the bps count itself (250 for 2.5%), an int, so no
          rounding creeps in the way a stored float would.

    Yields:
        A BasisPoint wrapping the stored int. EMPTY when the slot was never
        written.

    Example:
        >>> from nu.std.fin import PyBasisPoint
        >>> class Fees(nu.Shape):
        ...     taker = nu.mem.BasisPointRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Fees)
        >>> _ = nu.run(Fees.taker.set(PyBasisPoint(250)), ctx)
        >>> data
        {'taker': 250}
        >>> nu.run(Fees.taker.apply(1000), ctx)[0]
        25.0
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a BasisPoint slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> PyBasisPoint:
        """Wrap the stored int back as a BasisPoint."""
        return raw if isinstance(raw, PyBasisPoint) else PyBasisPoint(int(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyBasisPoint | int]) -> SetCmd:
        """Write a BasisPoint into the slot as a raw int of bps.

        Notes:
            - A plain Python value is converted at tree-build time; a Nu
              operand gets a ``ToInt`` node instead.
        """
        val = ToInt(value) if isinstance(value, Nu) else int(value)
        return SetCmd(self, val)


class PercentageRef(ItemRef, PercentageForm):
    """A Percentage slot in the dict substrate, stored as a raw float.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as the percentage number itself (2.5 for 2.5%), not the
          0.025 decimal fraction.

    Yields:
        A Percentage wrapping the stored float. EMPTY when the slot was never
        written.

    Example:
        >>> from nu.std.fin import PyPercentage
        >>> class Fees(nu.Shape):
        ...     rate = nu.mem.PercentageRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Fees)
        >>> _ = nu.run(Fees.rate.set(PyPercentage(2.5)), ctx)
        >>> data
        {'rate': 2.5}
        >>> nu.run(Fees.rate.to_bps(), ctx)[0]
        250
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a Percentage slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> PyPercentage:
        """Wrap the stored float back as a Percentage."""
        return raw if isinstance(raw, PyPercentage) else PyPercentage(float(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[PyPercentage | float]) -> SetCmd:
        """Write a Percentage into the slot as a raw float.

        Notes:
            - A plain Python value is converted at tree-build time; a Nu
              operand gets a ``ToFloat`` node instead.
        """
        val = ToFloat(value) if isinstance(value, Nu) else float(value)
        return SetCmd(self, val)


# =============================================================================
# DATETIME REFS
# =============================================================================


class DateRef(ItemRef, DateForm):
    """A date slot in the dict substrate, stored as an ISO string.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as ``YYYY-MM-DD``, so the data dict stays readable and
          sorts by date lexicographically.
        - A datetime written here is stringified whole, and reading it back
          as a date then fails on the time part; write ``d.date()``.

    Yields:
        A date, parsed from the stored ISO string. EMPTY when the slot was
        never written.

    Example:
        >>> from datetime import date
        >>> class Trade(nu.Shape):
        ...     day = nu.mem.DateRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Trade)
        >>> _ = nu.run(Trade.day.set(date(2024, 1, 2)), ctx)
        >>> data
        {'day': '2024-01-02'}
        >>> nu.run(Trade.day.year(), ctx)[0]
        2024
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a date slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> date:
        """Parse the stored ISO str back to a date."""
        return raw if isinstance(raw, date) else date.fromisoformat(str(raw))

    def set(self, value: Arg[date | str]) -> SetCmd:
        """Write a date into the slot as an ISO string.

        Notes:
            - A date is formatted at tree-build time and anything else is
              passed through ``str``; a Nu operand gets a ``ToStr`` node, so
              what it yields has to be something ``date.fromisoformat``
              accepts.
        """
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, date) else str(value)
        return SetCmd(self, val)


class DatetimeRef(ItemRef, DatetimeForm):
    """A datetime slot in the dict substrate, stored as an ISO string.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Whatever tzinfo the value carries rides along in the ISO string and
          comes back with it; a naive datetime stays naive.
        - A number found in the slot is read as a UTC epoch timestamp, so a
          dict filled from a feed that stores epochs still lifts.

    Yields:
        A datetime, parsed from the stored ISO string. EMPTY when the slot
        was never written.

    Example:
        >>> from datetime import datetime
        >>> class Event(nu.Shape):
        ...     at = nu.mem.DatetimeRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Event)
        >>> _ = nu.run(Event.at.set(datetime(2024, 1, 2, 3, 4)), ctx)
        >>> data
        {'at': '2024-01-02T03:04:00'}
        >>> nu.run(Event.at.hour(), ctx)[0]
        3
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a datetime slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> datetime:
        """Parse the stored ISO str (or epoch) back to a datetime."""
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=UTC)
        return datetime.fromisoformat(str(raw))

    def set(self, value: Arg[datetime | str]) -> SetCmd:
        """Write a datetime into the slot as an ISO string.

        Notes:
            - A datetime is formatted at tree-build time and anything else is
              passed through ``str``; a Nu operand gets a ``ToStr`` node.
        """
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, datetime) else str(value)
        return SetCmd(self, val)


class TimeRef(ItemRef, TimeForm):
    """A time-of-day slot in the dict substrate, stored as an ISO string.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Stored as ``HH:MM:SS``, with microseconds and a tz offset appended
          only when the value carries them.

    Yields:
        A time, parsed from the stored ISO string. EMPTY when the slot was
        never written.

    Example:
        >>> from datetime import time
        >>> class Session(nu.Shape):
        ...     opens = nu.mem.TimeRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Session)
        >>> _ = nu.run(Session.opens.set(time(9, 30)), ctx)
        >>> data
        {'opens': '09:30:00'}
        >>> nu.run(Session.opens.minute(), ctx)[0]
        30
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a time-of-day slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> time:
        """Parse the stored ISO str back to a time."""
        return raw if isinstance(raw, time) else time.fromisoformat(str(raw))

    def set(self, value: Arg[time | str]) -> SetCmd:
        """Write a time into the slot as an ISO string.

        Notes:
            - A time is formatted at tree-build time and anything else is
              passed through ``str``; a Nu operand gets a ``ToStr`` node.
        """
        if isinstance(value, Nu):
            val = ToStr(value)
        else:
            val = value.isoformat() if isinstance(value, time) else str(value)
        return SetCmd(self, val)


class TimedeltaRef(ItemRef, TimedeltaForm):
    """A timedelta slot in the dict substrate, stored as total seconds.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - One float of seconds, so the stored number compares and sums
          directly without going through the ref.
        - Sub-microsecond precision is lost, the same as
          ``timedelta.total_seconds()`` loses it.

    Yields:
        A timedelta rebuilt from the stored seconds. EMPTY when the slot was
        never written.

    Example:
        >>> from datetime import timedelta
        >>> class Job(nu.Shape):
        ...     took = nu.mem.TimedeltaRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Job)
        >>> _ = nu.run(Job.took.set(timedelta(minutes=90)), ctx)
        >>> data
        {'took': 5400.0}
        >>> nu.run(Job.took.seconds(), ctx)[0]
        5400
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a timedelta slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> timedelta:
        """Rebuild the timedelta from the stored total-seconds float."""
        return raw if isinstance(raw, timedelta) else timedelta(seconds=float(raw))  # type: ignore[arg-type]

    def set(self, value: Arg[timedelta | float]) -> SetCmd:
        """Write a timedelta into the slot as a float of total seconds.

        Notes:
            - A timedelta is converted at tree-build time and a plain number
              is taken as seconds already; a Nu operand gets a
              ``TimedeltaTotalSeconds`` node, so it must yield a timedelta.
        """
        if isinstance(value, Nu):
            val = TimedeltaTotalSeconds(value)
        elif isinstance(value, timedelta):
            val = value.total_seconds()
        else:
            val = float(value)
        return SetCmd(self, val)


class TimezoneRef(ItemRef, TimezoneForm):
    """A fixed-offset timezone slot, stored as its ``UTC±HH:MM`` string.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Only fixed offsets survive: the stored text is what ``str`` gives a
          ``datetime.timezone``, and a named zone (``ZoneInfo``) written here
          does not come back as one.
        - Reading parses the offset by hand, hours and optional minutes, so
          ``"UTC"`` alone lifts to UTC.

    Yields:
        A timezone with the stored offset. EMPTY when the slot was never
        written.

    Example:
        >>> from datetime import timedelta, timezone
        >>> class Site(nu.Shape):
        ...     tz = nu.mem.TimezoneRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Site)
        >>> _ = nu.run(Site.tz.set(timezone(timedelta(hours=5, minutes=30))), ctx)
        >>> data
        {'tz': 'UTC+05:30'}
        >>> nu.run(Site.tz, ctx)[0]
        datetime.timezone(datetime.timedelta(seconds=19800))
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a timezone slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> timezone:
        """Parse the stored offset str back to a timezone."""
        return raw if isinstance(raw, timezone) else _parse_timezone(str(raw))

    def set(self, value: Arg[timezone | str]) -> SetCmd:
        """Write a timezone into the slot as its offset string.

        Notes:
            - A plain Python value goes through ``str`` at tree-build time; a
              Nu operand gets a ``ToStr`` node.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


# =============================================================================
# PATH AND UUID REFS
# =============================================================================


class PathRef(ItemRef, PathForm):
    """A filesystem path slot in the dict substrate, stored as a plain str.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Lifted to a ``PurePath``, so the flavour follows the machine
          reading it: the same stored string is a PurePosixPath on Linux and
          a PureWindowsPath on Windows.
        - Pure means no filesystem: the calls take the path apart and put it
          back together, they never touch disk.

    Yields:
        A PurePath built from the stored string. EMPTY when the slot was
        never written.

    Example:
        >>> from pathlib import PurePath
        >>> class Cfg(nu.Shape):
        ...     root = nu.mem.PathRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Cfg)
        >>> _ = nu.run(Cfg.root.set(PurePath("/srv/app.toml")), ctx)
        >>> data
        {'root': '/srv/app.toml'}
        >>> nu.run(Cfg.root.name(), ctx)[0]
        'app.toml'
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a path slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> PurePath:
        """Parse the stored str back to a PurePath."""
        from pathlib import PurePath

        return raw if isinstance(raw, PurePath) else PurePath(str(raw))

    def set(self, value: Arg[PurePath | str]) -> SetCmd:
        """Write a path into the slot as a plain string.

        Notes:
            - A plain Python value goes through ``str`` at tree-build time; a
              Nu operand gets a ``ToStr`` node.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)


class UUIDRef(ItemRef, UUIDForm):
    """A UUID slot in the dict substrate, stored as its hyphenated string.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - Parsing on read is ``uuid.UUID(str)``, which takes the hyphenated
          form, a bare hex run, or a URN, so a hand-filled dict is forgiving.

    Yields:
        A UUID parsed from the stored string. EMPTY when the slot was never
        written.

    Example:
        >>> import uuid
        >>> class Row(nu.Shape):
        ...     rid = nu.mem.UUIDRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Row)
        >>> _ = nu.run(Row.rid.set(uuid.UUID(int=1)), ctx)
        >>> data
        {'rid': '00000000-0000-0000-0000-000000000001'}
        >>> nu.run(Row.rid.int_(), ctx)[0]
        1
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        parent_ref: RefBase | None = None,
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
        """Declare a UUID slot in a Shape class body."""
        return Slot(cls)  # type: ignore[return-value]

    def _lift(self, raw: object) -> UUID:
        """Parse the stored str back to a UUID."""
        import uuid

        return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))

    def set(self, value: Arg[UUID | str]) -> SetCmd:
        """Write a UUID into the slot as its hyphenated string.

        Notes:
            - A plain Python value goes through ``str`` at tree-build time; a
              Nu operand gets a ``ToStr`` node.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
