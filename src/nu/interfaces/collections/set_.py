"""SetI, FrozenSetI - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interfaces.collections_abc import MutableSetBase, SetLikeBase
from nu.interfaces.interface import Interface


if TYPE_CHECKING:
    from nu.interfaces.primitives.bool_ import BoolI
    from nu.interfaces.special.any_ import AnyI
    from nu.terms import FrozenSetArg, Nu, SetArg


__all__ = [
    "FrozenSetI",
    "SetI",
]


class SetI[T](
    MutableSetBase[set[T], T, "SetI[T]", "AnyI"],
    Interface[set[T]],
):
    """Set interface. Mutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> SetI[T]:
        return SetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.interfaces.special.any_ import AnyI

        return AnyI(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import GtOp

        return BoolI(GtOp(self, other))

    def __lt__(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import LtOp

        return BoolI(LtOp(self, other))

    def __ge__(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import GeOp

        return BoolI(GeOp(self, other))

    def __le__(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import LeOp

        return BoolI(LeOp(self, other))

    def eq(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import EqOp

        return BoolI(EqOp(self, other))

    def ne(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import NeOp

        return BoolI(NeOp(self, other))

    def is_(self, other: SetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import IdCompOp

        return BoolI(IdCompOp(self, other))


class FrozenSetI[T](
    SetLikeBase[frozenset[T], T, "FrozenSetI[T]", "AnyI"],
    Interface[frozenset[T]],
):
    """FrozenSet interface. Immutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSetI[T]:
        return FrozenSetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.interfaces.special.any_ import AnyI

        return AnyI(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import GtOp

        return BoolI(GtOp(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import LtOp

        return BoolI(LtOp(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import GeOp

        return BoolI(GeOp(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import LeOp

        return BoolI(LeOp(self, other))

    def eq(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import EqOp

        return BoolI(EqOp(self, other))

    def ne(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import NeOp

        return BoolI(NeOp(self, other))

    def is_(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interfaces.primitives.bool_ import BoolI
        from nu.ops import IdCompOp

        return BoolI(IdCompOp(self, other))
