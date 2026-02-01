"""Example demonstrating mapping and sequence support in Shape system.

This example shows:
1. Mapping of primitives (dict-like)
2. Mapping of shapes (dict of structured objects)
3. Sequence of primitives (list-like)
4. Sequence of shapes (list of structured objects)
5. Nested collections (infinite nesting)
"""

from __future__ import annotations

from datetime import datetime

from every_dict import RefBase
from every_dict import Shape as DictShape
from every_pv import PrimitiveRef
from every_pv import Shape as PVShape
from everyabc import Arg, FloatArg, Ref, RValue, Sentinel, Shape, Slot, StrArg, Term
from everybase import (
    AddOp,
    FloatValue,
    FuncCallOp,
    ItemGetOp,
    ItemSetCmd,
    MethodCallOp,
    StrValue,
    ToFloatOp,
    ToStrOp,
    TypeBase,
    ValueBase,
    ensure_term,
)
from everyshape import ItemRef


# =============================================
# Type
# =============================================


class DatetimeType(TypeBase[datetime | Sentinel]):
    @classmethod
    def from_timestamp(cls, ts: FloatArg) -> DatetimeValue:
        if isinstance(ts, str):
            val = float(ts)
        elif isinstance(ts, float):
            val = ts
        elif isinstance(ts, Term):
            val = FloatValue(ToFloatOp(ts))
        else:
            raise TypeError(f"Unknown type for datetime: {type(ts)}")
        return DatetimeValue(FuncCallOp(datetime.fromtimestamp, val))

    @classmethod
    def from_iso(cls, ts: StrArg) -> DatetimeValue:
        if isinstance(ts, Sentinel):
            raise TypeError
        return DatetimeValue(FuncCallOp(datetime.fromisoformat, ts))

    def to_timestamp(self) -> FloatValue:
        return FloatValue(MethodCallOp(self, "timestamp"))

    def to_iso(self) -> StrValue:
        return StrValue(ToStrOp(self))

    def __add__(self, obj: Arg[DatetimeType]) -> DatetimeValue:
        if isinstance(obj, float):
            val = obj
        elif isinstance(obj, DatetimeType):
            val = obj.to_timestamp()
        else:
            val = obj

        return DatetimeValue.from_timestamp(AddOp(self.to_timestamp(), val))


# =============================================
# Computed Value
# =============================================


class DatetimeValue(ValueBase, DatetimeType):
    pass


# =============================================
# Ref
# =============================================


class DatetimeRefBase(ItemRef[datetime, DatetimeValue], DatetimeType):
    def set(self, value: datetime | RValue[str | Sentinel]) -> DatetimeValue:
        if isinstance(value, datetime):
            val = str(value)
        elif isinstance(value, float):
            val = str(value)
        elif isinstance(value, str):
            val = value
        elif isinstance(value, DatetimeType):
            val = value.to_iso()
        else:
            raise TypeError(f"Unknown type for datetime: {type(value)}")
        return DatetimeValue(ItemSetCmd(self, ensure_term(val)))

    def get(self) -> DatetimeValue:
        return DatetimeValue.from_iso(ItemGetOp(self))


# =============================================
# Refs for PV and Dict substrates
# =============================================


class PVDatetimeRef(DatetimeRefBase, PrimitiveRef):
    pass


class DictDatetimeRef(DatetimeRefBase, RefBase):
    pass


# =============================================
# Slots for PV and Dict substrates
# =============================================


class _PVDatetimeSlot(Slot):
    def __init__(self) -> None:
        super().__init__()
        self.value_type = str

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> PVDatetimeRef:
        return PVDatetimeRef(
            address=self.name,
            value_type=self.value_type,
            parent=parent_ref,
            shape=owner_shape,
        )


def PVDatetimeSlot() -> PVDatetimeRef:  # noqa: N802
    return _PVDatetimeSlot()  # type: ignore[reportReturnType]


class _DictDatetimeSlot(Slot):
    def __init__(self) -> None:
        super().__init__()
        self.value_type = str

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> DictDatetimeRef:
        return DictDatetimeRef(
            address=self.name,
            parent=parent_ref,
            shape=owner_shape,
        )


def DictDatetimeSlot() -> DictDatetimeRef:  # noqa: N802
    return _DictDatetimeSlot()  # type: ignore[reportReturnType]


# =============================================
# Example
# =============================================


class SymbolInfo(DictShape):
    """Individual symbol information."""

    test_dt = DictDatetimeSlot()


class PVSymbolInfo(PVShape):
    """Individual symbol information."""

    test_dt = PVDatetimeSlot()


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
