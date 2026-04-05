"""TupleI - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ..collections_abc import SequenceBase
from ..interface import Interface


if TYPE_CHECKING:
    from ..primitives.bool_ import BoolI
    from ..special.any_ import AnyI
    from nu.terms import IntArg, Nu, TupleArg


__all__ = [
    "TupleI",
]


class TupleI[*Ts](
    SequenceBase[tuple[*Ts], object, "ListI[object]", "AnyI"],
    Interface[tuple[*Ts]],
):
    """Tuple interface. Immutable sequence + comparable."""

    def _wrap_sliceable_result(self, operand: Nu) -> TupleI:
        return TupleI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from ..special.any_ import AnyI

        return AnyI(operand)

    @overload
    def __getitem__(self, key: IntArg) -> AnyI: ...
    @overload
    def __getitem__(self, key: slice) -> TupleI: ...
    def __getitem__(self, key: IntArg | slice) -> AnyI | TupleI:
        from ..special.any_ import AnyI
        from nu.ops import AtOp, SliceOp

        if isinstance(key, slice):
            return TupleI(SliceOp(self, key.start, key.stop, key.step))
        return AnyI(AtOp(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import GtOp

        return BoolI(GtOp(self, other))

    def __lt__(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import LtOp

        return BoolI(LtOp(self, other))

    def __ge__(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import GeOp

        return BoolI(GeOp(self, other))

    def __le__(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import LeOp

        return BoolI(LeOp(self, other))

    def eq(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import EqOp

        return BoolI(EqOp(self, other))

    def ne(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import NeOp

        return BoolI(NeOp(self, other))

    def is_(self, other: TupleArg[*Ts]) -> BoolI:
        from ..primitives.bool_ import BoolI
        from nu.ops import IdCompOp

        return BoolI(IdCompOp(self, other))
