"""Date Ref."""

from __future__ import annotations

from datetime import date

from term.ops import MethodCallOp
from term.types import IntType, StrType

from every._abc import StrArg
from everybase.ref import CollectionItemRefBase
from everybase.ref.comp import GetOp, TypedSetCmd
from everybase.ref.ref import PrimitiveRef

from .args import DateArg
from .type import DateType


__all__ = [
    "DateRef",
]


class DateRef(CollectionItemRefBase[date, DateType], PrimitiveRef):
    """Reference to a date value in storage."""

    def set(self, value: DateArg) -> DateType:
        """Set the date value."""
        if isinstance(value, date):
            val = value.isoformat()
        else:
            val = MethodCallOp(value, "isoformat")
        return DateType(TypedSetCmd(self, val))

    def get(self) -> DateType:
        """Get the date value."""
        return DateType.from_iso(GetOp(self))

    # =========================================================================
    # CONVENIENCE METHODS (delegate to get())
    # =========================================================================

    def year(self) -> IntType:
        return self.get().year()

    def month(self) -> IntType:
        return self.get().month()

    def day(self) -> IntType:
        return self.get().day()

    def weekday(self) -> IntType:
        return self.get().weekday()

    def isoweekday(self) -> IntType:
        return self.get().isoweekday()

    def toordinal(self) -> IntType:
        return self.get().toordinal()

    def isoformat(self) -> StrType:
        return self.get().isoformat()

    def strftime(self, fmt: StrArg) -> StrType:
        return self.get().strftime(fmt)
