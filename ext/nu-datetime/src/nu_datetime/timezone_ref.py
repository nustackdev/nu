"""Timezone type for timezone values.

Pattern:
    TimezoneType = Object[timezone] + EqualableBase + timezone operations
    TimezoneValue = ValueBase + TimezoneType (computed results)

Note: Timezones are not orderable (no <, >, <=, >=).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from nu import Sentinel
from nu.abc import (
    EqualableBase,
    NoneValue,
    Object,
    StrValue,
    ValueBase,
)


if TYPE_CHECKING:
    from nu import Term

    from .args import DatetimeArg, TimedeltaArg


__all__ = [
    "TimezoneType",
    "TimezoneValue",
]


class TimezoneType(
    EqualableBase["timezone | TimezoneType"],
    Object[timezone | Sentinel],
):
    """Abstract type for timezone operations.

    Supports timezone operations and offset calculations.
    Uses *Type in arguments (loose variance), returns *Value (specific).

    Note: Timezones are not orderable (no <, >, <=, >=).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def utc(cls) -> TimezoneValue:
        """Create a TimezoneValue for UTC."""
        return TimezoneValue(UTC)

    @classmethod
    def from_offset(
        cls,
        hours: int | Term[int] = 0,
        minutes: int | Term[int] = 0,
        name: str | Term[str] | None = None,
    ) -> TimezoneValue:
        """Create a TimezoneValue from hour/minute offset."""
        from nu.abc import FuncCallOp

        from .timedelta_ref import TimedeltaValue

        offset = TimedeltaValue.from_components(hours=hours, minutes=minutes)
        if name is not None:
            return TimezoneValue(FuncCallOp(timezone, offset, name))
        return TimezoneValue(FuncCallOp(timezone, offset))

    @classmethod
    def from_timedelta(
        cls,
        offset: TimedeltaArg,
        name: str | Term[str] | None = None,
    ) -> TimezoneValue:
        """Create a TimezoneValue from a timedelta offset."""
        from nu.abc import FuncCallOp

        from .timedelta_ref import TimedeltaValue

        if isinstance(offset, timedelta):
            offset = TimedeltaValue(offset)
        if name is not None:
            return TimezoneValue(FuncCallOp(timezone, offset, name))
        return TimezoneValue(FuncCallOp(timezone, offset))

    # =========================================================================
    # METHODS
    # =========================================================================

    def tzname(self, dt: DatetimeArg | None = None) -> StrValue:
        """Get the timezone name."""
        from nu.abc import MethodCallOp

        from .datetime_ref import DatetimeValue

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeValue(dt)
        else:
            dt_arg = dt
        return StrValue(MethodCallOp(self, "tzname", dt_arg))

    def utcoffset(self, dt: DatetimeArg | None = None) -> TimedeltaValue:
        """Get the UTC offset as timedelta."""
        from nu.abc import MethodCallOp

        from .datetime_ref import DatetimeValue
        from .timedelta_ref import TimedeltaValue

        if dt is None:
            dt_arg = None
        elif isinstance(dt, datetime):
            dt_arg = DatetimeValue(dt)
        else:
            dt_arg = dt
        return TimedeltaValue(MethodCallOp(self, "utcoffset", dt_arg))

    def dst(self, dt: DatetimeArg | None = None) -> NoneValue:
        """Get the daylight saving time offset (returns None for fixed-offset timezones)."""
        return NoneValue()


# =============================================================================
# VALUE (computed results)
# =============================================================================


class TimezoneValue(ValueBase, TimezoneType):
    """Computed timezone value (Python memory substrate)."""

    pass


# Forward references
if TYPE_CHECKING:
    from .timedelta_ref import TimedeltaValue
