"""IteratorI - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu


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
        from nu.ops import ToListOp

        from .list_ import ListI

        return ListI(ToListOp(self))

    def to_set(self) -> SetI[T]:
        from nu.ops import ToSetOp

        from .set_ import SetI

        return SetI(ToSetOp(self))

    def to_tuple(self) -> TupleI:
        from nu.ops import ToTupleOp

        from .tuple_ import TupleI

        return TupleI(ToTupleOp(self))
