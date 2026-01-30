"""List ref base combining sequence traits.

ListRefBase = RefBase[list] + Sequence + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.capabilities import ComparableBase, SequenceBase

from .base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import AnyRef, BoolRef, ListRef


__all__ = [
    "ListRefBase",
]


class ListRefBase[T](
    SequenceBase[T, "ListRef[T]"],
    ComparableBase["list[T] | ListRef[T]"],
    RefBase[list[T]],
):
    """Abstract base for list refs.

    Combines sequence traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_sliceable_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_element_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)

    def __add__(self, other: list[T] | ListRefBase[T]) -> ListRef[T]:
        from everybase.morphisms import AddOp
        from everybase.py.list import ListRef

        return ListRef(AddOp[list[T]](self, other))

    def __radd__(self, other: list[T]) -> ListRef[T]:
        from everybase.morphisms import AddOp
        from everybase.py.list import ListRef

        return ListRef(AddOp(other, self))

    @overload
    def __getitem__(self, key: int) -> AnyRef: ...
    @overload
    def __getitem__(self, key: slice) -> ListRef[T]: ...
    def __getitem__(self, key: int | slice) -> AnyRef | ListRef[T]:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.py.any import AnyRef
        from everybase.py.list import ListRef

        if isinstance(key, slice):
            return ListRef(SliceOp(self, key.start, key.stop, key.step))
        return AnyRef(AtOp(self, key))
