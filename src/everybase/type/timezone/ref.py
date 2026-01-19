"""Timezone Ref."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef
from everyterm.ops import MethodCallOp
from everyterm.term import Arg
from everyterm.types import NoneType, StrType

from .args import TimezoneArg
from .type import TimezoneType


if TYPE_CHECKING:
    from everybase.type.timedelta import TimedeltaType


__all__ = [
    "TimezoneRef",
]


type DatetimeArg = Arg[datetime | None]


class TimezoneRef(CollectionItemRefBase[timezone, TimezoneType], PrimitiveRef):
    """Reference to a timezone value in storage."""

    def set(self, value: TimezoneArg) -> TimezoneType:
        """Set the timezone value.

        Stores as total seconds offset from UTC.
        """
        if isinstance(value, timezone):
            # Get offset in seconds
            offset = value.utcoffset(None)
            val = offset.total_seconds() if offset else 0
        else:
            # For TimezoneType, get utcoffset and total_seconds
            val = MethodCallOp(MethodCallOp(value, "utcoffset", NoneType()), "total_seconds")
        return TimezoneType(TypedSetCmd(self, val))

    def get(self) -> TimezoneType:
        """Get the timezone value."""
        from everybase.type.timedelta import TimedeltaType

        offset = TimedeltaType.from_seconds(GetOp(self))
        return TimezoneType.from_timedelta(offset)

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def tzname(self, dt: DatetimeArg = None) -> StrType:
        return self.get().tzname(dt)

    def utcoffset(self, dt: DatetimeArg = None) -> TimedeltaType:
        return self.get().utcoffset(dt)
