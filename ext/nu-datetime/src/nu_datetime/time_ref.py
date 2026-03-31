"""Time type for time values.

Pattern:
    TimeType = Object[time] + ComparableBase + time operations
    TimeValue = ValueBase + TimeType (computed results)
"""

from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from nu import Sentinel
from nu.abc import (
    ComparableBase,
    IntValue,
    Object,
    StrValue,
    ValueBase,
)


if TYPE_CHECKING:
    from nu import Term


__all__ = [
    "TimeType",
    "TimeValue",
]


class TimeType(
    ComparableBase["time | TimeType"],
    Object[time | Sentinel],
):
    """Abstract type for time operations.

    Supports comparison operations and time-specific methods.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def from_iso(cls, iso_str: str | Term[str]) -> TimeValue:
        """Create a TimeValue from an ISO format string (HH:MM:SS[.ffffff])."""
        from nu.abc import FuncCallOp

        def _safe_fromisoformat(s: object) -> time | Sentinel:
            if not isinstance(s, str):
                from nu import EMPTY

                return EMPTY
            return time.fromisoformat(s)

        return TimeValue(FuncCallOp(_safe_fromisoformat, iso_str))

    @classmethod
    def from_components(
        cls,
        hour: int | Term[int] = 0,
        minute: int | Term[int] = 0,
        second: int | Term[int] = 0,
        microsecond: int | Term[int] = 0,
    ) -> TimeValue:
        """Create a TimeValue from time components."""
        from nu.abc import FuncCallOp

        return TimeValue(FuncCallOp(time, hour, minute, second, microsecond))

    @classmethod
    def midnight(cls) -> TimeValue:
        """Create a TimeValue for midnight (00:00:00)."""
        return cls.from_components(0, 0, 0)

    @classmethod
    def noon(cls) -> TimeValue:
        """Create a TimeValue for noon (12:00:00)."""
        return cls.from_components(12, 0, 0)

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def hour(self) -> IntValue:
        """Get the hour component (0-23)."""
        from nu.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "hour"))

    def minute(self) -> IntValue:
        """Get the minute component (0-59)."""
        from nu.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "minute"))

    def second(self) -> IntValue:
        """Get the second component (0-59)."""
        from nu.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "second"))

    def microsecond(self) -> IntValue:
        """Get the microsecond component (0-999999)."""
        from nu.abc import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "microsecond"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self, timespec: str | Term[str] = "auto") -> StrValue:
        """Convert to ISO 8601 format string."""
        from nu.abc import MethodCallOp

        return StrValue(MethodCallOp(self, "isoformat", timespec))

    def strftime(self, fmt: str | Term[str]) -> StrValue:
        """Format time as string."""
        from nu.abc import MethodCallOp

        return StrValue(MethodCallOp(self, "strftime", fmt))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        hour: int | Term[int] | None = None,
        minute: int | Term[int] | None = None,
        second: int | Term[int] | None = None,
        microsecond: int | Term[int] | None = None,
    ) -> TimeValue:
        """Create a new time with some components replaced."""
        from nu.abc import MethodCallOp

        kwargs = {}
        if hour is not None:
            kwargs["hour"] = hour
        if minute is not None:
            kwargs["minute"] = minute
        if second is not None:
            kwargs["second"] = second
        if microsecond is not None:
            kwargs["microsecond"] = microsecond
        return TimeValue(MethodCallOp(self, "replace", **kwargs))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class TimeValue(ValueBase, TimeType):
    """Computed time value (Python memory substrate)."""

    pass
