"""Example demonstrating custom Ref types with the Ref.slot() pattern.

This example shows how to add a custom type (datetime) to the PV substrate.
The pattern:
    1. Define a Type class with operators (DatetimeType)
    2. Define a Value class for computed results (DatetimeValue)
    3. Define a RefBase with get/set methods (DatetimeRefBase)
    4. Subclass RefBase with the substrate's PrimitiveRef and add .slot()

The .slot() classmethod uses Slot internally — users never
need to create Slot classes manually.
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

import nu_virtuals as ebv
from nu import Arg, FloatArg, Sentinel, StrArg
from nu.abc import (
    AddOp,
    FloatI,
    FloatI,
    FuncCallOp,
    MethodCallOp,
    StrI,
    StrI,
    ToFloatOp,
    ToStrOp,
    TypeBase,
    Interface,
    ensure_term,
)
from nu.shape import ItemRef, ItemStoreCmd, Shape, Slot


# =============================================
# Type
# =============================================


class DatetimeType(TypeBase[datetime | Sentinel]):
    @classmethod
    def from_timestamp(cls, ts: FloatArg | StrArg) -> DatetimeValue:
        if isinstance(ts, (float, FloatI)):
            val = ts
        elif isinstance(ts, str):
            val = float(ts)
        elif isinstance(ts, StrI):
            val = FloatI(ToFloatOp(ts))
        else:
            raise TypeError(f"Unsupported type for datetime: {type(ts)}")
        return DatetimeValue(FuncCallOp(datetime.fromtimestamp, val))

    @classmethod
    def from_iso(cls, ts: StrArg) -> DatetimeValue:
        if not isinstance(ts, (str, StrI)):
            raise TypeError(f"from_iso requires str type, got {type(ts)}")
        return DatetimeValue(FuncCallOp(datetime.fromisoformat, ts))

    def to_timestamp(self) -> FloatI:
        return FloatI(MethodCallOp(self, "timestamp"))

    def to_iso(self) -> StrI:
        return StrI(ToStrOp(self))

    def __add__(self, obj: Arg[DatetimeType]) -> DatetimeValue:
        if isinstance(obj, (float, FloatI)):
            val = obj
        elif isinstance(obj, str):
            val = float(obj)
        elif isinstance(obj, StrI):
            val = FloatI(ToFloatOp(obj))
        elif isinstance(obj, DatetimeType):
            val = obj.to_timestamp()
        else:
            raise TypeError(f"Unsupported type for datetime addition: {type(obj)}")
        return DatetimeValue.from_timestamp(FloatI(AddOp(self.to_timestamp(), val)))


# =============================================
# Computed Value
# =============================================


class DatetimeValue(Interface, DatetimeType):
    pass


# =============================================
# Ref
# =============================================


class DatetimeRefBase(ItemRef[datetime, DatetimeValue], DatetimeType):
    def store(self, value: Arg[datetime] | StrArg | FloatArg) -> DatetimeValue:
        if isinstance(value, datetime):
            val = str(value)
        elif isinstance(value, DatetimeType):
            val = value.to_iso()
        elif isinstance(value, float):
            val = str(value)
        elif isinstance(value, FloatI):
            val = StrI(ToStrOp(value))
        elif isinstance(value, StrI):
            val = value
        else:
            raise TypeError(f"Unsupported type for datetime: {type(value)}")
        return DatetimeValue(ItemStoreCmd(self, ensure_term(val)))

    def coerce(self, raw: str) -> datetime:
        """Convert ISO string from storage to datetime."""
        return datetime.fromisoformat(raw)


# =============================================
# PV Ref with .slot() pattern
# =============================================


class VirtualsDatetimeRef(DatetimeRefBase, ebv.PrimitiveRef):
    """PV substrate datetime ref with .slot() factory."""

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for this ref type."""
        return Slot(cls, value_type=str)  # type: ignore[return-value]


# =============================================
# Shape definition using Ref.slot()
# =============================================


class PVSymbolInfo(Shape):
    """Symbol info using PV substrate."""

    test_dt = VirtualsDatetimeRef.slot()


# =============================================
# Execution
# =============================================


async def main():
    from virtuals import View
    from virtuals.views import DictView

    from nu_virtuals.presets import text_storage
    from nu import Context

    with text_storage(".db") as storage:
        ctx = Context()

        print("=== Write (Atomic → transaction) ===")
        with storage.transaction() as tx:
            root_view = DictView.open_root(tx)
            ctx = ctx.bind(root_view, View, PVSymbolInfo)

            await PVSymbolInfo.test_dt.store(datetime.now()).execute(ctx)
            print("Get: ", await PVSymbolInfo.test_dt.execute(ctx))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
