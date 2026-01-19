"""Datetime Ref."""

from __future__ import annotations

from datetime import datetime

from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef
from everyterm.ops import MethodCallOp
from everyterm.term import RValue, StrArg
from everyterm.types import FloatType, IntType, StrType

from .args import DatetimeArg
from .type import DatetimeType


__all__ = [
    "DatetimeRef",
]


class DatetimeRef(CollectionItemRefBase[datetime, DatetimeType], PrimitiveRef):
    """Reference to a datetime value in storage."""

    def set(self, value: DatetimeArg) -> DatetimeType:
        """Set the datetime value."""
        if isinstance(value, datetime):
            val = value.isoformat()
        else:
            val = MethodCallOp(value, "isoformat")
        return DatetimeType(TypedSetCmd(self, val))

    def get(self) -> DatetimeType:
        """Get the datetime value."""
        return DatetimeType.from_iso(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def year(self) -> IntType:
        return self.get().year()

    def month(self) -> IntType:
        return self.get().month()

    def day(self) -> IntType:
        return self.get().day()

    def hour(self) -> IntType:
        return self.get().hour()

    def minute(self) -> IntType:
        return self.get().minute()

    def second(self) -> IntType:
        return self.get().second()

    def weekday(self) -> IntType:
        return self.get().weekday()

    def timestamp(self) -> FloatType:
        return self.get().timestamp()

    def isoformat(self, sep: StrArg = "T", timespec: StrArg = "auto") -> StrType:
        return self.get().isoformat(sep, timespec)

    def date(self) -> RValue:
        return self.get().date()

    def time(self) -> RValue:
        return self.get().time()

    def strftime(self, fmt: StrArg) -> StrType:
        return self.get().strftime(fmt)
