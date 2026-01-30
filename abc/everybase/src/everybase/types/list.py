"""List ref base combining sequence traits.

ListType = TypeBase[list] + Sequence + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.capabilities import ComparableBase, SequenceBase

from ._base import TypeBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.values import AnyValue, BoolValue, ListValue


__all__ = [
    "ListType",
]


class ListType[T](
    SequenceBase[T, "ListValue[T]"],
    ComparableBase["list[T] | ListValue[T]"],
    TypeBase[list[T]],
):
    """Abstract base for list refs.

    Combines sequence traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolValue:
        from everybase.values import BoolValue

        return BoolValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        from everybase.values import ListValue

        return ListValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> ListValue:
        from everybase.values import ListValue

        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        from everybase.values import AnyValue

        return AnyValue(operand)

    def __add__(self, other: list[T] | ListType[T]) -> ListValue[T]:
        from everybase.morphisms import AddOp
        from everybase.values import ListValue

        return ListValue(AddOp[list[T]](self, other))

    def __radd__(self, other: list[T]) -> ListValue[T]:
        from everybase.morphisms import AddOp
        from everybase.values import ListValue

        return ListValue(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> AnyValue: ...
    @overload
    def __getitem__(self, key: slice) -> ListValue[T]: ...
    def __getitem__(self, key: int | slice) -> AnyValue | ListValue[T]:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.values import AnyValue, ListValue

        if isinstance(key, slice):
            return ListValue(SliceOp(self, key.start, key.stop, key.step))
        return AnyValue(AtOp(self, key))
