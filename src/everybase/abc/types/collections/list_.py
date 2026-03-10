"""List ref base combining sequence traits.

ListType = TypeBase[list] + MutableSequence + Clearable + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ...capabilities import ComparableBase
from ...collections import MutableSequenceBase
from ..base import TypeBase


if TYPE_CHECKING:
    from everybase.core import IntArg, ListArg, Term

    from ...values import AnyValue, BoolValue, ListValue


__all__ = [
    "ListType",
]


class ListType[T](
    MutableSequenceBase[list[T], T, "ListValue[T]", "AnyValue"],
    # ClearableBase,
    ComparableBase["ListArg[T]"],
    TypeBase[list[T]],
):
    """Abstract base for list refs.

    Combines sequence traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from ...values import BoolValue

        return BoolValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> ListValue:
        from ...values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from ...values import AnyValue

        return AnyValue(operand)

    def __add__(self, other: ListArg[T]) -> ListValue[T]:
        from ...morphisms import AddOp
        from ...values import ListValue

        return ListValue(AddOp[list[T]](self, other))

    def __radd__(self, other: ListArg[T]) -> ListValue[T]:
        from ...morphisms import AddOp
        from ...values import ListValue

        return ListValue(AddOp(other, self))

    @overload
    def __getitem__(self, key: IntArg) -> AnyValue: ...
    @overload
    def __getitem__(self, key: slice) -> ListValue[T]: ...
    def __getitem__(self, key: IntArg | slice) -> AnyValue | ListValue[T]:
        from ...morphisms import AtOp, SliceOp
        from ...values import AnyValue, ListValue

        if isinstance(key, slice):
            return ListValue(SliceOp(self, key.start, key.stop, key.step))
        return AnyValue(AtOp(self, key))
