"""Date type for date values.

Pattern:
    DateType = Object[date] + ComparableBase + date operations
    DateValue = ValueBase + DateType (computed results)
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from nu import Sentinel
from nu import (
    ComparableBase,
    IntValue,
    Object,
    StrValue,
    ValueBase,
)


if TYPE_CHECKING:
    from nu import Nu

    from .args import DateArg, TimedeltaArg


__all__ = [
    "DateType",
    "DateValue",
]


class DateType(
    ComparableBase["date | DateType"],
    Object[date | Sentinel],
):
    """Abstract type for date operations.

    Supports comparison operations and date-specific methods.
    Uses *Type in arguments (loose variance), returns *Value (specific).
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def today(cls) -> DateValue:
        """Create a DateValue for today."""
        from nu import FuncCallOp

        return DateValue(FuncCallOp(date.today))

    @classmethod
    def from_iso(cls, iso_str: str | Nu[str]) -> DateValue:
        """Create a DateValue from an ISO format string (YYYY-MM-DD)."""
        from nu import FuncCallOp

        def _safe_fromisoformat(s: object) -> date | Sentinel:
            if not isinstance(s, str):
                from nu import EMPTY

                return EMPTY
            return date.fromisoformat(s)

        return DateValue(FuncCallOp(_safe_fromisoformat, iso_str))

    @classmethod
    def from_ordinal(cls, ordinal: int | Nu[int]) -> DateValue:
        """Create a DateValue from a Gregorian ordinal."""
        from nu import FuncCallOp

        return DateValue(FuncCallOp(date.fromordinal, ordinal))

    @classmethod
    def from_timestamp(cls, timestamp: float | Nu[float]) -> DateValue:
        """Create a DateValue from a POSIX timestamp."""
        from nu import FuncCallOp

        return DateValue(FuncCallOp(date.fromtimestamp, timestamp))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntValue:
        """Get the year component."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "year"))

    def month(self) -> IntValue:
        """Get the month component (1-12)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "month"))

    def day(self) -> IntValue:
        """Get the day component (1-31)."""
        from nu import FuncCallOp

        return IntValue(FuncCallOp(getattr, self, "day"))

    def weekday(self) -> IntValue:
        """Get the day of week (Monday=0, Sunday=6)."""
        from nu import MethodCallOp

        return IntValue(MethodCallOp(self, "weekday"))

    def isoweekday(self) -> IntValue:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        from nu import MethodCallOp

        return IntValue(MethodCallOp(self, "isoweekday"))

    def toordinal(self) -> IntValue:
        """Get the Gregorian ordinal."""
        from nu import MethodCallOp

        return IntValue(MethodCallOp(self, "toordinal"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self) -> StrValue:
        """Convert to ISO 8601 format string (YYYY-MM-DD)."""
        from nu import MethodCallOp

        return StrValue(MethodCallOp(self, "isoformat"))

    def strftime(self, fmt: str | Nu[str]) -> StrValue:
        """Format date as string."""
        from nu import MethodCallOp

        return StrValue(MethodCallOp(self, "strftime", fmt))

    def ctime(self) -> StrValue:
        """Return ctime-style string."""
        from nu import MethodCallOp

        return StrValue(MethodCallOp(self, "ctime"))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: int | Nu[int] | None = None,
        month: int | Nu[int] | None = None,
        day: int | Nu[int] | None = None,
    ) -> DateValue:
        """Create a new date with some components replaced."""
        from nu import MethodCallOp

        kwargs = {}
        if year is not None:
            kwargs["year"] = year
        if month is not None:
            kwargs["month"] = month
        if day is not None:
            kwargs["day"] = day
        return DateValue(MethodCallOp(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DateValue:
        """Add a timedelta to this date."""
        from datetime import timedelta

        from nu import AddOp

        from .timedelta_ref import TimedeltaValue

        if isinstance(delta, timedelta):
            delta = TimedeltaValue(delta)
        return DateValue(AddOp(self, delta))

    def __sub__(self, other: DateArg | TimedeltaArg) -> DateValue | TimedeltaValue:
        """Subtract a date or timedelta."""
        from datetime import timedelta

        from nu import SubOp

        from .timedelta_ref import TimedeltaValue

        if isinstance(other, date):
            other = DateValue(other)
        if isinstance(other, timedelta):
            other = TimedeltaValue(other)
        if isinstance(other, DateType):
            return TimedeltaValue(SubOp(self, other))
        return DateValue(SubOp(self, other))


# =============================================================================
# VALUE (computed results)
# =============================================================================


class DateValue(ValueBase, DateType):
    """Computed date value (Python memory substrate)."""

    pass


# Forward references
if TYPE_CHECKING:
    from .timedelta_ref import TimedeltaValue
