"""Tuple ref base combining sequence traits.

TupleType = TypeBase[tuple] + Sequence + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.capabilities import ComparableBase, SequenceBase

from ._base import TypeBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import AnyValue, BoolValue, ListValue, TupleValue


__all__ = [
    "TupleType",
]


class TupleType[*Ts](
    SequenceBase[object, "ListValue[object]"],
    ComparableBase["tuple"],
    TypeBase[tuple[*Ts]],
):
    """Abstract base for tuple refs.

    Combines sequence traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> TupleValue:
        from everybase.values import TupleValue

        return TupleValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from everybase.values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from everybase.values import AnyValue

        return AnyValue(operand)

    @overload
    def __getitem__(self, key: int) -> AnyValue: ...
    @overload
    def __getitem__(self, key: slice) -> TupleValue: ...
    def __getitem__(self, key: int | slice) -> AnyValue | TupleValue:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.values import AnyValue, TupleValue

        if isinstance(key, slice):
            return TupleValue(SliceOp(self, key.start, key.stop, key.step))
        return AnyValue(AtOp(self, key))
