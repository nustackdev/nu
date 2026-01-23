"""Timezone ref base for timezone values.

TimezoneRefBase = RefBase[timezone] + Equalable + timezone operations.
Note: Timezones are not orderable (no <, >, <=, >=).
Stored as offset string for serialization.
"""

from __future__ import annotations

from abc import ABC
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Equalable


if TYPE_CHECKING:
    from every import Term
    from everybase.py import StrRef

    from .args import DatetimeArg, TimedeltaArg
    from .py.refs import TimedeltaRef, TimezoneRef


__all__ = [
    "TimezoneRefBase",
]


class TimezoneRefBase(
    Equalable["timezone | TimezoneRef"],
    RefBase[timezone],
    ABC,
):
    """Abstract base for timezone refs.

    Supports timezone operations and offset calculations.
    Stored as offset string for serialization.

    Note: Timezones are not orderable (no <, >, <=, >=).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def utc(cls) -> TimezoneRef:
        """Create a TimezoneRef for UTC."""
        from .py.refs import TimezoneRef

        return TimezoneRef(UTC)

    @classmethod
    def from_offset(
        cls,
        hours: int | Term[int] = 0,
        minutes: int | Term[int] = 0,
        name: str | Term[str] | None = None,
    ) -> TimezoneRef:
        """Create a TimezoneRef from hour/minute offset."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import TimedeltaRef, TimezoneRef

        offset = TimedeltaRef.from_components(hours=hours, minutes=minutes)
        if name is not None:
            return TimezoneRef(FuncCallOp(timezone, offset, name))
        return TimezoneRef(FuncCallOp(timezone, offset))

    @classmethod
    def from_timedelta(
        cls,
        offset: TimedeltaArg,
        name: str | Term[str] | None = None,
    ) -> TimezoneRef:
        """Create a TimezoneRef from a timedelta offset."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import TimedeltaRef, TimezoneRef

        if isinstance(offset, timedelta):
            offset = TimedeltaRef(offset)
        if name is not None:
            return TimezoneRef(FuncCallOp(timezone, offset, name))
        return TimezoneRef(FuncCallOp(timezone, offset))

    # =========================================================================
    # METHODS
    # =========================================================================

    def tzname(self, dt: DatetimeArg | None = None) -> StrRef:
        """Get the timezone name."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        from .py.refs import DatetimeRef

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeRef(dt)
        else:
            dt_arg = dt
        return StrRef(MethodCallOp(self, "tzname", dt_arg))

    def utcoffset(self, dt: DatetimeArg | None = None) -> TimedeltaRef:
        """Get the UTC offset as timedelta."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DatetimeRef, TimedeltaRef

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeRef(dt)
        else:
            dt_arg = dt
        return TimedeltaRef(MethodCallOp(self, "utcoffset", dt_arg))

    def dst(self, dt: DatetimeArg | None = None) -> TimedeltaRef:
        """Get the daylight saving time offset (returns None for fixed-offset timezones)."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import NoneRef

        from .py.refs import DatetimeRef

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeRef(dt)
        else:
            dt_arg = dt
        # dst() returns None for fixed-offset timezones
        return NoneRef(MethodCallOp(self, "dst", dt_arg))
