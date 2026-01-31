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

from everyterm.shape import Shape, Slot
from everyterm.term import PrimitiveRef, Ref, RValue, TypedValue
from everyterm.term.comps.callable import FuncCallOp, MethodCallOp, TypedSetCmd
from everyterm.term.comps.core import AddOp
from everyterm.term.comps.ref import GetOp
from everyterm.term.refs import CollectionItemRefBase
from everyterm.term.types import CoreBase, FloatType, literal

import everybase as e
from everyshape.typing import Sentinel


# =============================================
# Type, Shape, Ref
# =============================================


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


class DatetimeRef(CollectionItemRefBase[datetime, DatetimeValue], PrimitiveRef):
    def set(self, value: datetime | RValue[str | Sentinel]) -> DatetimeValue:
        if isinstance(value, datetime):
            val = str(value)
        else:
            val = value
        return DatetimeValue(TypedSetCmd(self, literal(val)))

    def get(self) -> DatetimeValue:
        return DatetimeValue.from_iso(GetOp(self))


class _DatetimeSlot(Slot):
    def __init__(self) -> None:
        super().__init__()
        self.value_type = str

    def create_ref(
        self,
        owner_shape: type[Shape],
        parent_ref: Ref | None = None,
    ) -> DatetimeRef:
        return DatetimeRef(
            address=self.name,
            value_type=self.value_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )


def DatetimeSlot() -> DatetimeRef:  # noqa: N802
    return _DatetimeSlot()  # type: ignore[reportReturnType]


class SymbolInfo(Shape):
    """Individual symbol information."""

    test_dt = DatetimeSlot()


# =============================================
# Flow
# =============================================

flow = e.f.Seq(
    SymbolInfo.test_dt.set(datetime.now()),
    SymbolInfo.test_dt.get(),
    e.f.Print("res: {}", SymbolInfo.test_dt.get() + SymbolInfo.test_dt.get()),
)

# =============================================
# Execution
# =============================================


async def main():
    from everybase.top import regular_provider, text_storage

    with text_storage(".db12") as storage:
        await flow.start_flow(regular_provider(storage))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
