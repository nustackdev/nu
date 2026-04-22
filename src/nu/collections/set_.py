"""SetI, FrozenSetI - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import TypedNu

from .abc import MutableSetI, SetLikeI


if TYPE_CHECKING:
    from nu.primitives import AnyI, BoolI
    from nu.terms import FrozenSetArg, Nu, SetArg


__all__ = [
    "FrozenSetI",
    "SetI",
]


class SetI[T](
    MutableSetI[set[T], T, "SetI[T]", "AnyI"],
    TypedNu[set[T]],
):
    """Set interface. Mutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> SetI[T]:
        return SetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: SetArg[T]) -> BoolI:
        from nu.interactions import IdComp
        from nu.primitives import BoolI

        return BoolI(IdComp(self, other))


class FrozenSetI[T](
    SetLikeI[frozenset[T], T, "FrozenSetI[T]", "AnyI"],
    TypedNu[frozenset[T]],
):
    """FrozenSet interface. Immutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSetI[T]:
        return FrozenSetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: FrozenSetArg[T]) -> BoolI:
        from nu.interactions import IdComp
        from nu.primitives import BoolI

        return BoolI(IdComp(self, other))
