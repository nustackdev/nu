"""Date Type."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from everybase.type.timedelta import TimedeltaArg
from everyterm.ops import AddOp, FuncCallOp, MethodCallOp, SubOp
from everyterm.term import FloatArg, IntArg, StrArg
from everyterm.types import BaseType, ComparisonBase, IntType, StrType
from everyterm.typing import Sentinel

from .args import DateArg


if TYPE_CHECKING:
    from everybase.type.timedelta import TimedeltaType


__all__ = [
    "DateType",
]


class DateType(
    ComparisonBase["date | DateType"],
    BaseType[date | Sentinel],
):
    """Type representing a date.

    Supports comparison operations and date-specific methods.
    Stored as ISO format string for serialization.

    Example:
        >>> d = DateType.today()
        >>> d.year()         # IntType
        >>> d.weekday()      # IntType
        >>> d.isoformat()    # StrType
        >>> d > other_date   # BoolType
    """

    # =========================================================================
    # CONSTRUCTORS
    # =========================================================================

    @classmethod
    def today(cls) -> DateType:
        """Create a DateType for today."""
        return cls(FuncCallOp(date.today))

    @classmethod
    def from_iso(cls, iso_str: StrArg) -> DateType:
        """Create a DateType from an ISO format string (YYYY-MM-DD)."""
        return cls(FuncCallOp(date.fromisoformat, iso_str))

    @classmethod
    def from_ordinal(cls, ordinal: IntArg) -> DateType:
        """Create a DateType from a Gregorian ordinal."""
        return cls(FuncCallOp(date.fromordinal, ordinal))

    @classmethod
    def from_timestamp(cls, timestamp: FloatArg) -> DateType:
        """Create a DateType from a POSIX timestamp."""
        return cls(FuncCallOp(date.fromtimestamp, timestamp))

    # =========================================================================
    # COMPONENT ACCESSORS
    # =========================================================================

    def year(self) -> IntType:
        """Get the year component."""
        return IntType(FuncCallOp(getattr, self, "year"))

    def month(self) -> IntType:
        """Get the month component (1-12)."""
        return IntType(FuncCallOp(getattr, self, "month"))

    def day(self) -> IntType:
        """Get the day component (1-31)."""
        return IntType(FuncCallOp(getattr, self, "day"))

    def weekday(self) -> IntType:
        """Get the day of week (Monday=0, Sunday=6)."""
        return IntType(MethodCallOp(self, "weekday"))

    def isoweekday(self) -> IntType:
        """Get the ISO day of week (Monday=1, Sunday=7)."""
        return IntType(MethodCallOp(self, "isoweekday"))

    def toordinal(self) -> IntType:
        """Get the Gregorian ordinal."""
        return IntType(MethodCallOp(self, "toordinal"))

    # =========================================================================
    # CONVERSIONS
    # =========================================================================

    def isoformat(self) -> StrType:
        """Convert to ISO 8601 format string (YYYY-MM-DD)."""
        return StrType(MethodCallOp(self, "isoformat"))

    def strftime(self, fmt: StrArg) -> StrType:
        """Format date as string."""
        return StrType(MethodCallOp(self, "strftime", fmt))

    def ctime(self) -> StrType:
        """Return ctime-style string."""
        return StrType(MethodCallOp(self, "ctime"))

    # =========================================================================
    # MANIPULATION
    # =========================================================================

    def replace(
        self,
        year: IntArg | None = None,
        month: IntArg | None = None,
        day: IntArg | None = None,
    ) -> DateType:
        """Create a new date with some components replaced."""
        kwargs = {}
        if year is not None:
            kwargs["year"] = year
        if month is not None:
            kwargs["month"] = month
        if day is not None:
            kwargs["day"] = day
        return DateType(MethodCallOp(self, "replace", **kwargs))

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, delta: TimedeltaArg) -> DateType:
        """Add a timedelta to this date."""
        from datetime import timedelta

        from everybase.type.timedelta import TimedeltaType

        if isinstance(delta, timedelta):
            delta = TimedeltaType(delta)
        return DateType(AddOp(self, delta))

    def __sub__(self, other: DateArg | TimedeltaArg) -> DateType | TimedeltaType:
        """Subtract a date or timedelta."""
        from datetime import timedelta

        from everybase.type.timedelta import TimedeltaType

        if isinstance(other, date):
            other = DateType(other)
        if isinstance(other, timedelta):
            other = TimedeltaType(other)
        if isinstance(other, DateType):
            return TimedeltaType(SubOp(self, other))
        return DateType(SubOp(self, other))
