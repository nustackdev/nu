"""TupleI - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.interface import TypedNu

from .abc import SequenceI


if TYPE_CHECKING:
    from nu.primitives import AnyI, BoolI
    from nu.terms import IntArg, Nu, TupleArg


__all__ = [
    "TupleI",
]


class TupleI[*Ts](
    SequenceI[tuple[*Ts], object, "ListI[object]", "AnyI"],
    TypedNu[tuple[*Ts]],
):
    """Tuple interface. Immutable sequence + comparable."""

    def _wrap_sliceable_result(self, operand: Nu) -> TupleI:
        return TupleI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    @overload
    def __getitem__(self, key: IntArg) -> AnyI: ...
    @overload
    def __getitem__(self, key: slice) -> TupleI: ...
    def __getitem__(self, key: IntArg | slice) -> AnyI | TupleI:
        from nu.ops import AtOp, SliceOp
        from nu.primitives import AnyI

        if isinstance(key, slice):
            return TupleI(SliceOp(self, key.start, key.stop, key.step))
        return AnyI(AtOp(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import GtOp
        from nu.primitives import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import LtOp
        from nu.primitives import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import GeOp
        from nu.primitives import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import LeOp
        from nu.primitives import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import EqOp
        from nu.primitives import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import NeOp
        from nu.primitives import BoolI

        return BoolI(NeOp(self, other))

    def is_(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.ops import IdCompOp
        from nu.primitives import BoolI

        return BoolI(IdCompOp(self, other))
