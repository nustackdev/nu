"""ListI - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import TypedNu

from .abc import MutableSequenceI


if TYPE_CHECKING:
    from nu.primitives import AnyI, BoolI
    from nu.terms import IntArg, ListArg, Nu


__all__ = [
    "ListI",
]


class ListI[T](
    MutableSequenceI[list[T], T, "ListI[T]", "AnyI"],
    TypedNu[list[T]],
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
        from nu import Add

        return ListI(Add(self, other))

    def __radd__(self, other: ListArg[T]) -> ListI[T]:
        from nu import Add

        return ListI(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> AnyI: ...
    @overload
    def __getitem__(self, key: slice) -> ListI[T]: ...
    def __getitem__(self, key: IntArg | slice) -> AnyI | ListI[T]:
        from nu import At, Slice
        from nu.primitives import AnyI

        if isinstance(key, slice):
            return ListI(Slice(self, key.start, key.stop, key.step))
        return AnyI(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> BoolI:
        from nu import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: ListArg[T]) -> BoolI:
        from nu import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: ListArg[T]) -> BoolI:
        from nu import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: ListArg[T]) -> BoolI:
        from nu import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: ListArg[T]) -> BoolI:
        from nu import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: ListArg[T]) -> BoolI:
        from nu import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: ListArg[T]) -> BoolI:
        from nu import IdComp
        from nu.primitives import BoolI

        return BoolI(IdComp(self, other))
