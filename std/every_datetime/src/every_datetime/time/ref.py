"""Time Ref."""

from __future__ import annotations

from datetime import time

from term.ops import MethodCallOp
from term.types import IntType, StrType

from every._abc import StrArg
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .args import TimeArg
from .type import TimeType


__all__ = [
    "TimeRef",
]


class TimeRef(CollectionItemRefBase[time, TimeType], PrimitiveRef):
    """Reference to a time value in storage."""

    def set(self, value: TimeArg) -> TimeType:
        """Set the time value."""
        if isinstance(value, time):
            val = value.isoformat()
        else:
            val = MethodCallOp(value, "isoformat")
        return TimeType(TypedSetCmd(self, val))

    def get(self) -> TimeType:
        """Get the time value."""
        return TimeType.from_iso(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def hour(self) -> IntType:
        return self.get().hour()

    def minute(self) -> IntType:
        return self.get().minute()

    def second(self) -> IntType:
        return self.get().second()

    def microsecond(self) -> IntType:
        return self.get().microsecond()

    def isoformat(self, timespec: StrArg = "auto") -> StrType:
        return self.get().isoformat(timespec)

    def strftime(self, fmt: StrArg) -> StrType:
        return self.get().strftime(fmt)
