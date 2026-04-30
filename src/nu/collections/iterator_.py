"""IteratorI - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from .list_ import ListI
    from .set_ import SetI
    from .tuple_ import TupleI


__all__ = [
    "IteratorI",
]


class IteratorI[T](Interface, TypedNu[Iterator[T]]):
    """Lazy iterator interface. Materializes via to_list/to_set/to_tuple."""

    def to_list(self) -> ListI[T]:
        from nu import ToList

        from .list_ import ListI

        return ListI(ToList(self))

    def to_set(self) -> SetI[T]:
        from nu import ToSet

        from .set_ import SetI

        return SetI(ToSet(self))

    def to_tuple(self) -> TupleI:
        from nu import ToTuple

        from .tuple_ import TupleI

        return TupleI(ToTuple(self))
