"""TupleI - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import TypedNu

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
        from nu.interactions import At, Slice
        from nu.primitives import AnyI

        if isinstance(key, slice):
            return TupleI(Slice(self, key.start, key.stop, key.step))
        return AnyI(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: TupleArg[*Ts]) -> BoolI:
        from nu.interactions import IdComp
        from nu.primitives import BoolI

        return BoolI(IdComp(self, other))
