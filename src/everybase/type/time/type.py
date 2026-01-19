"""Time Type."""

from __future__ import annotations

from datetime import time, timezone
from typing import TYPE_CHECKING

from everyterm.ops import FuncCallOp, MethodCallOp
from everyterm.term import IntArg, StrArg
from everyterm.types import BaseType, ComparisonBase, IntType, StrType
from everyterm.typing import Sentinel


if TYPE_CHECKING:
    from everybase.type.timezone import TimezoneArg

__all__ = [
    "TimeType",
]


class TimeType(
    ComparisonBase["time | TimeType"],
    BaseType[time | Sentinel],
):
    """Type representing a time.

    Supports comparison operations and time-specific methods.
    Stored as ISO format string for serialization.

    Example:
        >>> t = TimeType.from_iso("10:30:00")
        >>> t.hour()         # IntType
        >>> t.minute()       # IntType
        >>> t.isoformat()    # StrType
        >>> t > other_time   # BoolType
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_iso(cls, iso_str: StrArg) -> TimeType:
        """Create a TimeType from an ISO format string (HH:MM:SS[.ffffff])."""
        return cls(FuncCallOp(time.fromisoformat, iso_str))

    @classmethod
    def from_components(
        cls,
        hour: IntArg = 0,
        minute: IntArg = 0,
        second: IntArg = 0,
        microsecond: IntArg = 0,
        tzinfo: TimezoneArg | None = None,
    ) -> TimeType:
        """Create a TimeType from components."""
        if tzinfo is not None:
            if isinstance(tzinfo, timezone):
                from everybase.type.timezone import TimezoneType

                tzinfo = TimezoneType(tzinfo)
            return cls(FuncCallOp(time, hour, minute, second, microsecond, tzinfo))
        return cls(FuncCallOp(time, hour, minute, second, microsecond))

    @classmethod
    def midnight(cls) -> TimeType:
        """Create a TimeType for midnight (00:00:00)."""
        return cls.from_components(0, 0, 0)

    @classmethod
    def noon(cls) -> TimeType:
        """Create a TimeType for noon (12:00:00)."""
        return cls.from_components(12, 0, 0)

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def hour(self) -> IntType:
        """Get the hour component (0-23)."""
        return IntType(FuncCallOp(getattr, self, "hour"))

    def minute(self) -> IntType:
        """Get the minute component (0-59)."""
        return IntType(FuncCallOp(getattr, self, "minute"))

    def second(self) -> IntType:
        """Get the second component (0-59)."""
        return IntType(FuncCallOp(getattr, self, "second"))

    def microsecond(self) -> IntType:
        """Get the microsecond component (0-999999)."""
        return IntType(FuncCallOp(getattr, self, "microsecond"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self, timespec: StrArg = "auto") -> StrType:
        """Convert to ISO 8601 format string."""
        return StrType(MethodCallOp(self, "isoformat", timespec))

    def strftime(self, fmt: StrArg) -> StrType:
        """Format time as string."""
        return StrType(MethodCallOp(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        hour: IntArg | None = None,
        minute: IntArg | None = None,
        second: IntArg | None = None,
        microsecond: IntArg | None = None,
    ) -> TimeType:
        """Create a new time with some components replaced."""
        kwargs = {}
        if hour is not None:
            kwargs["hour"] = hour
        if minute is not None:
            kwargs["minute"] = minute
        if second is not None:
            kwargs["second"] = second
        if microsecond is not None:
            kwargs["microsecond"] = microsecond
        return TimeType(MethodCallOp(self, "replace", **kwargs))
