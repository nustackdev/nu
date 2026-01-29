"""Date ref base for date values.

DateRefBase = RefBase[date] + Comparable + date operations.
Stored as ISO format string (YYYY-MM-DD).
"""

from __future__ import annotations

from abc import ABC
from datetime import date
from typing import TYPE_CHECKING

from everybase.refs import RefBase
from everybase.traits import Comparable


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import IntRef, StrRef

    from .args import DateArg, TimedeltaArg
    from .py.refs import DateRef, TimedeltaRef


__all__ = [
    "DateRefBase",
]


class DateRefBase(
    Comparable["date | DateRef"],
    RefBase[date],
    ABC,
):
    """Abstract base for date refs.

    Supports comparison operations and date-specific methods.
    Stored as ISO format string for serialization.
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def today(cls) -> DateRef:
        """Create a DateRef for today."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DateRef

        return DateRef(FuncCallOp(date.today))

    @classmethod
    def from_iso(cls, iso_str: str | Term[str]) -> DateRef:
        """Create a DateRef from an ISO format string (YYYY-MM-DD)."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DateRef

        return DateRef(FuncCallOp(date.fromisoformat, iso_str))

    @classmethod
    def from_ordinal(cls, ordinal: int | Term[int]) -> DateRef:
        """Create a DateRef from a Gregorian ordinal."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DateRef

        return DateRef(FuncCallOp(date.fromordinal, ordinal))

    @classmethod
    def from_timestamp(cls, timestamp: float | Term[float]) -> DateRef:
        """Create a DateRef from a POSIX timestamp."""
        from everybase.morphisms import FuncCallOp

        from .py.refs import DateRef

        return DateRef(FuncCallOp(date.fromtimestamp, timestamp))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntRef:
        """Get the year component."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "year"))

    def month(self) -> IntRef:
        """Get the month component (1-12)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "month"))

    def day(self) -> IntRef:
        """Get the day component (1-31)."""
        from everybase.morphisms import FuncCallOp
        from everybase.py import IntRef

        return IntRef(FuncCallOp(getattr, self, "day"))

    def weekday(self) -> IntRef:
        """Get the day of week (Monday=0, Sunday=6)."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "weekday"))

    def isoweekday(self) -> IntRef:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "isoweekday"))

    def toordinal(self) -> IntRef:
        """Get the Gregorian ordinal."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import IntRef

        return IntRef(MethodCallOp(self, "toordinal"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self) -> StrRef:
        """Convert to ISO 8601 format string (YYYY-MM-DD)."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "isoformat"))

    def strftime(self, fmt: str | Term[str]) -> StrRef:
        """Format date as string."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "strftime", fmt))

    def ctime(self) -> StrRef:
        """Return ctime-style string."""
        from everybase.morphisms import MethodCallOp
        from everybase.py import StrRef

        return StrRef(MethodCallOp(self, "ctime"))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: int | Term[int] | None = None,
        month: int | Term[int] | None = None,
        day: int | Term[int] | None = None,
    ) -> DateRef:
        """Create a new date with some components replaced."""
        from everybase.morphisms import MethodCallOp

        from .py.refs import DateRef

        kwargs = {}
        if year is not None:
            kwargs["year"] = year
        if month is not None:
            kwargs["month"] = month
        if day is not None:
            kwargs["day"] = day
        return DateRef(MethodCallOp(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DateRef:
        """Add a timedelta to this date."""
        from datetime import timedelta

        from everybase.morphisms import AddOp

        from .py.refs import DateRef, TimedeltaRef

        if isinstance(delta, timedelta):
            delta = TimedeltaRef(delta)
        return DateRef(AddOp(self, delta))

    def __sub__(self, other: DateArg | TimedeltaArg) -> DateRef | TimedeltaRef:
        """Subtract a date or timedelta."""
        from datetime import timedelta

        from everybase.morphisms import SubOp

        from .py.refs import DateRef, TimedeltaRef

        if isinstance(other, date):
            other = DateRef(other)
        if isinstance(other, timedelta):
            other = TimedeltaRef(other)
        if isinstance(other, DateRef):
            return TimedeltaRef(SubOp(self, other))
        return DateRef(SubOp(self, other))
