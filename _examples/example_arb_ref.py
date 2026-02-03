"""Example demonstrating custom Ref types with the Ref.slot() pattern.

This example shows how to add a custom type (datetime) across substrates.
The pattern:
    1. Define a Type class with operators (DatetimeType)
    2. Define a Value class for computed results (DatetimeValue)
    3. Define a RefBase with get/set methods (DatetimeRefBase)
    4. For each substrate, subclass RefBase and add .slot()

The .slot() classmethod uses Slot internally — users never
need to create Slot classes manually.
"""

from __future__ import annotations

from datetime import datetime
from typing import Self

from every_dict import RefBase as DictRefBase
from every_dict import Shape
from every_pv import PrimitiveRef
from everyabc import Arg, FloatArg, Sentinel, StrArg
from everybase import (
    AddOp,
    FloatType,
    FloatValue,
    FuncCallOp,
    MethodCallOp,
    StrType,
    StrValue,
    ToFloatOp,
    ToStrOp,
    TypeBase,
    ValueBase,
    ensure_term,
)
from everyshape import ItemRef, Slot
from everyshape.morphisms import ItemGetOp, ItemSetCmd


# =============================================
# Type
# =============================================


class DatetimeType(TypeBase[datetime | Sentinel]):
    @classmethod
    def from_timestamp(cls, ts: FloatArg | StrArg) -> DatetimeValue:
        if isinstance(ts, (float, FloatType)):
            val = ts
        elif isinstance(ts, str):
            val = float(ts)
        elif isinstance(ts, StrType):
            val = FloatValue(ToFloatOp(ts))
        else:
            raise TypeError(f"Unsupported type for datetime: {type(ts)}")
        return DatetimeValue(FuncCallOp(datetime.fromtimestamp, val))

    @classmethod
    def from_iso(cls, ts: StrArg) -> DatetimeValue:
        if not isinstance(ts, (str, StrType)):
            raise TypeError(f"from_iso requires str type, got {type(ts)}")
        return DatetimeValue(FuncCallOp(datetime.fromisoformat, ts))

    def to_timestamp(self) -> FloatValue:
        return FloatValue(MethodCallOp(self, "timestamp"))

    def to_iso(self) -> StrValue:
        return StrValue(ToStrOp(self))

    def __add__(self, obj: Arg[DatetimeType]) -> DatetimeValue:
        if isinstance(obj, (float, FloatType)):
            val = obj
        elif isinstance(obj, str):
            val = float(obj)
        elif isinstance(obj, StrType):
            val = FloatValue(ToFloatOp(obj))
        elif isinstance(obj, DatetimeType):
            val = obj.to_timestamp()
        else:
            raise TypeError(f"Unsupported type for datetime addition: {type(obj)}")
        return DatetimeValue.from_timestamp(FloatValue(AddOp(self.to_timestamp(), val)))


# =============================================
# Computed Value
# =============================================


class DatetimeValue(ValueBase, DatetimeType):
    pass


# =============================================
# Ref
# =============================================


class DatetimeRefBase(ItemRef[datetime, DatetimeValue], DatetimeType):
    def set(self, value: Arg[datetime] | StrArg | FloatArg) -> DatetimeValue:
        if isinstance(value, datetime):
            val = str(value)
        elif isinstance(value, DatetimeType):
            val = value.to_iso()
        elif isinstance(value, float):
            val = str(value)
        elif isinstance(value, FloatType):
            val = StrValue(ToStrOp(value))
        elif isinstance(value, StrType):
            val = value
        else:
            raise TypeError(f"Unsupported type for datetime: {type(value)}")
        return DatetimeValue(ItemSetCmd(self, ensure_term(val)))

    def get(self) -> DatetimeValue:
        return DatetimeValue.from_iso(StrValue(ItemGetOp(self)))


# =============================================
# Substrate-specific Refs with .slot() pattern
# =============================================
#
# Each Ref class implements .slot() classmethod that returns a Slot.
# This eliminates the need for manual Slot classes per type per substrate.


class PVDatetimeRef(DatetimeRefBase, PrimitiveRef):
    """PV substrate datetime ref with .slot() factory."""

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for this ref type."""
        return Slot(cls, value_type=str)  # type: ignore[return-value]


class DictDatetimeRef(DatetimeRefBase, DictRefBase):
    """Dict substrate datetime ref with .slot() factory."""

    @classmethod
    def slot(cls) -> Self:
        """Create a slot for this ref type."""
        return Slot(cls)  # type: ignore[return-value]


# =============================================
# Shape definitions using Ref.slot()
# =============================================


class SymbolInfo(Shape):
    """Symbol info using dict substrate."""

    test_dt = DictDatetimeRef.slot()


class PVSymbolInfo(Shape):
    """Symbol info using PV substrate."""

    test_dt = PVDatetimeRef.slot()


# =============================================
# Execution
# =============================================


async def main():
    from time import perf_counter

    from everyabc import Context

    # ============
    # DICT
    # ============

    data: dict = {}
    ctx = Context().with_handle(dict, data, shape=SymbolInfo)

    print(data)

    start = perf_counter()
    set_expr = SymbolInfo.test_dt.set(datetime.now())
    for _ in range(100_000):
        await set_expr.execute(ctx)
    print("Took: ", perf_counter() - start)
    start = perf_counter()

    dd = {}
    dtn = datetime.now()
    for _ in range(100_000):
        dd["a"] = str(dtn)
    print("Took: ", perf_counter() - start)
    print(data)

    print("Get: ", await SymbolInfo.test_dt.get().execute(ctx))

    # ============
    # PV
    # ============

    from pv import View

    from every_pv.adapters.codecs import TextCodec as Codec
    from every_pv.adapters.storages.textdb import TextStorage as Storage
    from every_pv.views import DictView

    with Storage(".db", codec=Codec()) as storage:
        ctx = Context()

        print("=== Write (Atomic → transaction) ===")
        with storage.transaction() as tx:
            root_view = DictView.open_root(tx)
            ctx = ctx.with_handle(View, root_view, PVSymbolInfo)

            await PVSymbolInfo.test_dt.set(datetime.now()).execute(ctx)
            print("Get: ", await PVSymbolInfo.test_dt.get().execute(ctx))

    # ============
    # MIXED (O_o)
    # ============

    data: dict = {}
    ctx = Context().with_handle(dict, data, shape=SymbolInfo)

    with Storage(".db2", codec=Codec()) as storage:
        print("=== Write (Atomic → transaction) ===")
        with storage.transaction() as tx:
            root_view = DictView.open_root(tx)
            ctx = ctx.with_handle(View, root_view, PVSymbolInfo)

            await PVSymbolInfo.test_dt.set(datetime.now()).execute(ctx)
            await SymbolInfo.test_dt.set(PVSymbolInfo.test_dt.get()).execute(ctx)

            print("Get 1: ", await PVSymbolInfo.test_dt.get().execute(ctx))
            print("Get 2: ", await SymbolInfo.test_dt.get().execute(ctx))
            print(
                "Get +: ",
                await (SymbolInfo.test_dt.get() + PVSymbolInfo.test_dt.get()).execute(ctx),
            )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
