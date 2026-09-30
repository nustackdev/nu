"""The mem leaves for dates, times, durations and offsets, kept as text or seconds.

Each leaf pairs the ``nustd.datetime`` value form with the mem leaf and
translates at the boundary: ``set`` lowers the value, a read lifts it back, so
the ref is an operand of the real value throughout. The leaves live with
their library, not in ``nu.mem``: a container declared with the Python type
holds untyped ``ObjectRef`` children, and a container declared with the leaf
class holds these.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING

from nu.core import ToStr
from nu.domains.shape import SetCmd
from nu.lang import Nu
from nu.mem.refs import ItemRef
from nustd.datetime._offset import UTC, parse_timezone
from nustd.datetime.forms import date as DateForm
from nustd.datetime.forms import datetime as DatetimeForm
from nustd.datetime.forms import time as TimeForm
from nustd.datetime.forms import timedelta as TimedeltaForm
from nustd.datetime.forms import timezone as TimezoneForm
from nustd.datetime.interactions import TimedeltaTotalSeconds


if TYPE_CHECKING:
    from nu.lang import Arg


__all__ = ["DateRef", "DatetimeRef", "TimeRef", "TimedeltaRef", "TimezoneRef"]


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
        ...     day = nustd.datetime.mem.DateRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Trade)
        >>> _ = nu.run(Trade.day.set(date(2024, 1, 2)), ctx)
        >>> data
        {'day': '2024-01-02'}
        >>> nu.run(Trade.day.year(), ctx)[0]
        2024
    """

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
        ...     at = nustd.datetime.mem.DatetimeRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Event)
        >>> _ = nu.run(Event.at.set(datetime(2024, 1, 2, 3, 4)), ctx)
        >>> data
        {'at': '2024-01-02T03:04:00'}
        >>> nu.run(Event.at.hour(), ctx)[0]
        3
    """

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
        ...     opens = nustd.datetime.mem.TimeRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Session)
        >>> _ = nu.run(Session.opens.set(time(9, 30)), ctx)
        >>> data
        {'opens': '09:30:00'}
        >>> nu.run(Session.opens.minute(), ctx)[0]
        30
    """

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
        ...     took = nustd.datetime.mem.TimedeltaRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Job)
        >>> _ = nu.run(Job.took.set(timedelta(minutes=90)), ctx)
        >>> data
        {'took': 5400.0}
        >>> nu.run(Job.took.seconds(), ctx)[0]
        5400
    """

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
        ...     tz = nustd.datetime.mem.TimezoneRef.slot()
        >>> data = {}
        >>> ctx = nu.Context().bind(dict, data, Site)
        >>> _ = nu.run(Site.tz.set(timezone(timedelta(hours=5, minutes=30))), ctx)
        >>> data
        {'tz': 'UTC+05:30'}
        >>> nu.run(Site.tz, ctx)[0]
        datetime.timezone(datetime.timedelta(seconds=19800))
    """

    def _lift(self, raw: object) -> timezone:
        """Parse the stored offset str back to a timezone."""
        return raw if isinstance(raw, timezone) else parse_timezone(str(raw))

    def set(self, value: Arg[timezone | str]) -> SetCmd:
        """Write a timezone into the slot as its offset string.

        Notes:
            - A plain Python value goes through ``str`` at tree-build time; a
              Nu operand gets a ``ToStr`` node.
        """
        val = ToStr(value) if isinstance(value, Nu) else str(value)
        return SetCmd(self, val)
