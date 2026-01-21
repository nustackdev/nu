"""Tuple ref base combining sequence traits.

TupleRefBase = RefBase[tuple] + Sequence + Comparable

Returns concrete py types.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, overload

from everybase.traits import Comparable, Sequence

from .base import RefBase


if TYPE_CHECKING:
    from every import Term
    from everybase.py.any import AnyRef
    from everybase.py.bool import BoolRef
    from everybase.py.list import ListRef
    from everybase.py.tuple import TupleRef


__all__ = [
    "TupleRefBase",
]


class TupleRefBase[*Ts](
    Sequence[object, "ListRef[object]"],
    Comparable["tuple"],
    RefBase[tuple[*Ts]],
    ABC,
):
    """Abstract base for tuple refs.

    Combines sequence traits and returns concrete py types.
    """

    def _wrap_comparison_result(self, operand: Term) -> BoolRef:
        from everybase.py.bool import BoolRef

        return BoolRef(operand)

    def _wrap_sliceable_result(self, operand: Term) -> TupleRef:
        from everybase.py.tuple import TupleRef

        return TupleRef(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListRef:
        from everybase.py.list import ListRef

        return ListRef(operand)

    def _wrap_element_result(self, operand: Term) -> AnyRef:
        from everybase.py.any import AnyRef

        return AnyRef(operand)

    @overload
    def __getitem__(self, key: int) -> AnyRef: ...
    @overload
    def __getitem__(self, key: slice) -> TupleRef: ...
    def __getitem__(self, key: int | slice) -> AnyRef | TupleRef:
        from everybase.morphisms import AtOp, SliceOp
        from everybase.py.any import AnyRef
        from everybase.py.tuple import TupleRef

        if isinstance(key, slice):
            return TupleRef(SliceOp(self, key.start, key.stop, key.step))
        return AnyRef(AtOp(self, key))
