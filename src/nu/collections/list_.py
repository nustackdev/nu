"""ListI - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.interface import Interface

from .abc import MutableSequenceI


if TYPE_CHECKING:
    from nu.primitives import AnyI, BoolI
    from nu.terms import IntArg, ListArg, Nu


__all__ = [
    "ListI",
]


class ListI[T](
    MutableSequenceI[list[T], T, "ListI[T]", "AnyI"],
    Interface[list[T]],
):
    """List interface. Mutable sequence + comparable."""

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        return ListI(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListI:
        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> ListI[T]:
        from nu.ops import AddOp

        return ListI(AddOp(self, other))

    def __radd__(self, other: ListArg[T]) -> ListI[T]:
        from nu.ops import AddOp

        return ListI(AddOp(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> AnyI: ...
    @overload
    def __getitem__(self, key: slice) -> ListI[T]: ...
    def __getitem__(self, key: IntArg | slice) -> AnyI | ListI[T]:
        from nu.ops import AtOp, SliceOp
        from nu.primitives import AnyI

        if isinstance(key, slice):
            return ListI(SliceOp(self, key.start, key.stop, key.step))
        return AnyI(AtOp(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> BoolI:
        from nu.ops import GtOp
        from nu.primitives import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: ListArg[T]) -> BoolI:
        from nu.ops import LtOp
        from nu.primitives import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: ListArg[T]) -> BoolI:
        from nu.ops import GeOp
        from nu.primitives import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: ListArg[T]) -> BoolI:
        from nu.ops import LeOp
        from nu.primitives import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: ListArg[T]) -> BoolI:
        from nu.ops import EqOp
        from nu.primitives import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: ListArg[T]) -> BoolI:
        from nu.ops import NeOp
        from nu.primitives import BoolI

        return BoolI(NeOp(self, other))

    def is_(self, other: ListArg[T]) -> BoolI:
        from nu.ops import IdCompOp
        from nu.primitives import BoolI

        return BoolI(IdCompOp(self, other))
