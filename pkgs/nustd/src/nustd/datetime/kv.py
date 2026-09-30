"""The kv leaves for dates, times, durations and offsets, kept as text or seconds.

Each leaf pairs the ``nustd.datetime`` value form with the kv leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaves live with
their library, not in ``nustd.kv``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds these.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nustd.datetime._offset import UTC, parse_timezone
from nustd.datetime.forms import date as DateForm
from nustd.datetime.forms import datetime as DatetimeForm
from nustd.datetime.forms import time as TimeForm
from nustd.datetime.forms import timedelta as TimedeltaForm
from nustd.datetime.forms import timezone as TimezoneForm
from nustd.datetime.interactions import TimedeltaTotalSeconds
from nustd.kv.refs import ItemRef


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = ["DateRef", "DatetimeRef", "TimeRef", "TimedeltaRef", "TimezoneRef"]


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

    def _lift(self, raw: object) -> timezone:
        """Parse the stored offset str back to a timezone."""
        return raw if isinstance(raw, timezone) else parse_timezone(str(raw))

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
