"""Time ref base for time values.

TimeRefBase = RefBase[time] + Comparable + time operations.
Stored as ISO format string (HH:MM:SS[.ffffff]).
"""

from __future__ import annotations

from abc import ABC
from datetime import time, timezone
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from every import Term
    from everybase.py import IntRef, StrRef

    from .args import TimezoneArg
    from .py.refs import TimeRef


__all__ = [
    "TimeRefBase",
]


class TimeRefBase(
    Comparable["time | TimeRef"],
    RefBase[time],
    ABC,
):
    """Abstract base for time refs.

    Supports comparison operations and time-specific methods.
    Stored as ISO format string for serialization.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_iso(cls, iso_str: str | Term[str]) -> TimeRef:
        """Create a TimeRef from an ISO format string (HH:MM:SS[.ffffff])."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import TimeRef

        return TimeRef(FuncCallOp(time.fromisoformat, iso_str))

    @classmethod
    def from_components(
        cls,
        hour: int | Term[int] = 0,
        minute: int | Term[int] = 0,
        second: int | Term[int] = 0,
        microsecond: int | Term[int] = 0,
        tzinfo: TimezoneArg | None = None,
    ) -> TimeRef:
        """Create a TimeRef from components."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import TimeRef, TimezoneRef

        if tzinfo is not None:
            if isinstance(tzinfo, timezone):
                tzinfo = TimezoneRef(tzinfo)
            return TimeRef(FuncCallOp(time, hour, minute, second, microsecond, tzinfo))
        return TimeRef(FuncCallOp(time, hour, minute, second, microsecond))

    @classmethod
    def midnight(cls) -> TimeRef:
        """Create a TimeRef for midnight (00:00:00)."""
        return cls.from_components(0, 0, 0)

    @classmethod
    def noon(cls) -> TimeRef:
        """Create a TimeRef for noon (12:00:00)."""
        return cls.from_components(12, 0, 0)

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def hour(self) -> IntRef:
        """Get the hour component (0-23)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "hour"))

    def minute(self) -> IntRef:
        """Get the minute component (0-59)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "minute"))

    def second(self) -> IntRef:
        """Get the second component (0-59)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "second"))

    def microsecond(self) -> IntRef:
        """Get the microsecond component (0-999999)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "microsecond"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self, timespec: str | Term[str] = "auto") -> StrRef:
        """Convert to ISO 8601 format string."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "isoformat", timespec))

    def strftime(self, fmt: str | Term[str]) -> StrRef:
        """Format time as string."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        hour: int | Term[int] | None = None,
        minute: int | Term[int] | None = None,
        second: int | Term[int] | None = None,
        microsecond: int | Term[int] | None = None,
    ) -> TimeRef:
        """Create a new time with some components replaced."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import TimeRef

        kwargs = {}
        if hour is not None:
            kwargs["hour"] = hour
        if minute is not None:
            kwargs["minute"] = minute
        if second is not None:
            kwargs["second"] = second
        if microsecond is not None:
            kwargs["microsecond"] = microsecond
        return TimeRef(MethodCallOp(self, "replace", **kwargs))
