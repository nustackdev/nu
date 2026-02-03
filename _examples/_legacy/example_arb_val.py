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
from pathlib import Path

from everyterm.shape import Shape
from everyterm.term import Context, RValue, TypedValue
from everyterm.term.comps.callable import FuncCallOp, MethodCallOp
from everyterm.term.comps.core import AddOp
from everyterm.term.types import CoreBase, FloatType

from everybase.abc import DictView, StrSlot, TextCodec, TextStorage
from everyshape.typing import Sentinel


class DatetimeValue(CoreBase, TypedValue[datetime | Sentinel]):
    @classmethod
    def now(cls) -> DatetimeValue:
        return DatetimeValue(FuncCallOp(datetime.now))

    @classmethod
    def from_timestamp(cls, ts: float | RValue[float | Sentinel] | Sentinel) -> DatetimeValue:
        if isinstance(ts, Sentinel):
            raise TypeError
        return DatetimeValue(FuncCallOp(datetime.fromtimestamp, ts))

    @classmethod
    def from_iso(cls, ts: str | Sentinel | RValue[str | Sentinel]) -> DatetimeValue:
        if isinstance(ts, Sentinel):
            raise TypeError
        return DatetimeValue(FuncCallOp(datetime.fromisoformat, ts))

    def to_float(self) -> FloatType:
        return FloatType(MethodCallOp(self, "timestamp"))

    def __add__(self, obj: DatetimeValue | Sentinel) -> DatetimeValue:
        if isinstance(obj, Sentinel):
            raise TypeError
        return DatetimeValue(AddOp(self.to_float(), obj.to_float()))


class SymbolInfo(Shape):
    """Individual symbol information."""

    test_str = StrSlot()


if __name__ == "__main__":
    with (
        TextStorage(path=Path(".db_shape"), codec=TextCodec()) as storage,
        storage.transaction() as tx,
    ):
        root = DictView.open_root(tx)
        ctx = Context.create(root_view=root, storage_context=tx)

        res = SymbolInfo.test_str.set(DatetimeValue.now().to_str()).execute(ctx)
        print(res)
        res = SymbolInfo.test_str.get().execute(ctx)
        print(res)
        res = DatetimeValue.from_iso(SymbolInfo.test_str.get()).to_float().execute(ctx)
        print(res)
        res = (
            DatetimeValue.from_iso(SymbolInfo.test_str.get()).to_float()
            + DatetimeValue.from_iso(SymbolInfo.test_str.get()).to_float()
        ).execute(ctx)
        print(res)
        res = (
            DatetimeValue.from_iso(SymbolInfo.test_str.get())
            + DatetimeValue.from_iso(SymbolInfo.test_str.get())
        ).execute(ctx)
        print(res)

        print("###")
