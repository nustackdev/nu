"""Tuple ref base combining sequence traits.

TupleType = TypeBase[tuple] + Sequence + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ..capabilities import ComparableBase
from ..collections import SequenceBase
from .base import TypeBase


if TYPE_CHECKING:
    from everybase.core import IntArg, Term, TupleArg  # noqa: F401

    from ..values import AnyValue, BoolValue, ListValue, TupleValue


__all__ = [
    "TupleType",
]


class TupleType[*Ts](
    SequenceBase[tuple[*Ts], object, "ListValue[object]", "AnyValue"],
    ComparableBase["TupleArg[*Ts]"],
    TypeBase[tuple[*Ts]],
):
    """Abstract base for tuple refs.

    Combines sequence traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from ..values import BoolValue

        return BoolValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> TupleValue:
        from ..values import TupleValue

        return TupleValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from ..values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from ..values import AnyValue

        return AnyValue(operand)

    @overload
    def __getitem__(self, key: IntArg) -> AnyValue: ...
    @overload
    def __getitem__(self, key: slice) -> TupleValue: ...
    def __getitem__(self, key: IntArg | slice) -> AnyValue | TupleValue:
        from ..morphisms import AtOp, SliceOp
        from ..values import AnyValue, TupleValue

        if isinstance(key, slice):
            return TupleValue(SliceOp(self, key.start, key.stop, key.step))
        return AnyValue(AtOp(self, key))
