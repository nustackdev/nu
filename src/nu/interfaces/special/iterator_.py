"""IteratorI - lazy iterator interface."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from ..interface import Interface


if TYPE_CHECKING:
    from ..collections.list_ import ListI
    from ..collections.set_ import SetI
    from ..collections.tuple_ import TupleI


__all__ = [
    "IteratorI",
]


class IteratorI[T](Interface[Iterator[T]]):
    """Lazy iterator interface. Materializes via to_list/to_set/to_tuple."""

    def to_list(self) -> ListI[T]:
        from ..collections.list_ import ListI
        from nu.ops import ToListOp

        return ListI(ToListOp(self))

    def to_set(self) -> SetI[T]:
        from ..collections.set_ import SetI
        from nu.ops import ToSetOp

        return SetI(ToSetOp(self))

    def to_tuple(self) -> TupleI:
        from ..collections.tuple_ import TupleI
        from nu.ops import ToTupleOp

        return TupleI(ToTupleOp(self))
