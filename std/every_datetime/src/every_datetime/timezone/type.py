"""Timezone Type."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from term.ops import FuncCallOp, MethodCallOp
from term.types import BaseType, EqualableBase, NoneType, StrType
from term.typing import Sentinel

from every._abc import IntArg, StrArg


if TYPE_CHECKING:
    from everybase.type.datetime import DatetimeArg
    from everybase.type.timedelta import TimedeltaArg, TimedeltaType


__all__ = [
    "TimezoneType",
]


class TimezoneType(
    EqualableBase["timezone | TimezoneType"],
    BaseType[timezone | Sentinel],
):
    """Type representing a timezone.

    Supports timezone operations and offset calculations.
    Stored as offset string for serialization.

    Note: Timezones are not orderable (no <, >, <=, >=).

    Example:
        >>> tz = TimezoneType.utc()
        >>> tz = TimezoneType.from_offset(hours=5, minutes=30)
        >>> tz.tzname(None)  # StrType
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def utc(cls) -> TimezoneType:
        """Create a TimezoneType for UTC.

        Returns:
            TimezoneType representing UTC.

        Example:
            >>> TimezoneType.utc()
        """
        return cls(UTC)

    @classmethod
    def from_offset(
        cls,
        hours: IntArg = 0,
        minutes: IntArg = 0,
        name: StrArg | None = None,
    ) -> TimezoneType:
        """Create a TimezoneType from hour/minute offset.

        Args:
            hours: Hour offset from UTC (-23 to 23).
            minutes: Minute offset (0 to 59).
            name: Optional timezone name.

        Returns:
            TimezoneType from offset.

        Example:
            >>> TimezoneType.from_offset(hours=5, minutes=30)  # IST
            >>> TimezoneType.from_offset(hours=-5, name="EST")
        """
        from everybase.type.timedelta import TimedeltaType

        offset = TimedeltaType.from_components(hours=hours, minutes=minutes)
        if name is not None:
            return cls(FuncCallOp(timezone, TimedeltaType(offset), name))
        return cls(FuncCallOp(timezone, TimedeltaType(offset)))

    @classmethod
    def from_timedelta(
        cls,
        offset: TimedeltaArg,
        name: StrArg | None = None,
    ) -> TimezoneType:
        """Create a TimezoneType from a timedelta offset.

        Args:
            offset: Timedelta offset from UTC.
            name: Optional timezone name.

        Returns:
            TimezoneType from timedelta.

        Example:
            >>> td = TimedeltaType.from_components(hours=5)
            >>> TimezoneType.from_timedelta(td)
        """
        from everybase.type.timedelta import TimedeltaType

        if isinstance(offset, timedelta):
            offset = TimedeltaType(offset)
        if name is not None:
            return cls(FuncCallOp(timezone, offset, name))
        return cls(FuncCallOp(timezone, offset))

    # =========================================================================
    # METHODS
    # =========================================================================

    def tzname(self, dt: DatetimeArg | None = None) -> StrType:
        """Get the timezone name.

        Args:
            dt: Optional datetime (ignored for fixed-offset timezones).

        Returns:
            StrType containing the timezone name.
        """
        from everybase.type.datetime import DatetimeType

        if dt is None:
            dt = NoneType()
        elif isinstance(dt, datetime):
            dt = DatetimeType(dt)
        return StrType(MethodCallOp(self, "tzname", dt))

    def utcoffset(self, dt: DatetimeArg | None = None) -> TimedeltaType:
        """Get the UTC offset as timedelta.

        Args:
            dt: Optional datetime (ignored for fixed-offset timezones).

        Returns:
            TimedeltaType containing the offset.
        """
        from everybase.type.datetime import DatetimeType
        from everybase.type.timedelta import TimedeltaType

        if dt is None:
            dt = NoneType()
        elif isinstance(dt, datetime):
            dt = DatetimeType(dt)
        return TimedeltaType(MethodCallOp(self, "utcoffset", dt))

    def dst(self, dt: DatetimeArg | None = None) -> NoneType:
        """Get the DST offset.

        For fixed-offset timezones, this always returns None.

        Args:
            dt: Optional datetime (ignored for fixed-offset timezones).

        Returns:
            NoneType for fixed-offset timezones.
        """
        from everybase.type.datetime import DatetimeType

        if dt is None:
            dt = NoneType()
        elif isinstance(dt, datetime):
            dt = DatetimeType(dt)
        return NoneType(MethodCallOp(self, "dst", dt))
