"""Iterator type — lazy stream over elements.

IteratorType[T] wraps an Iterator[T] and provides materialization methods.
Transform morphisms (Map, Filter, Take, etc.) produce IteratorType values
that stream element-by-element without intermediate lists.

Materialization boundaries:
    .to_list() -> ListValue
    .to_set() -> SetValue
    .to_tuple() -> TupleValue
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from ..object import Object


if TYPE_CHECKING:
    from ...values import ListValue, SetValue, TupleValue


__all__ = [
    "IteratorType",
]


class IteratorType[T](
    Object[Iterator[T]],
):
    """Type for lazy iterator streams.

    Produced by transform morphisms (Map, Filter, Take, Drop, etc.).
    Consumed by terminal morphisms (Reduce, Sum, Min, Max, etc.)
    or materialized explicitly via to_list/to_set/to_tuple.
    """

    def to_list(self) -> ListValue[T]:
        """Materialize iterator into a list."""
        from nu.ops.builtins.conversion import ToListOp
        from ...values import ListValue

        return ListValue(ToListOp(self))

    def to_set(self) -> SetValue[T]:
        """Materialize iterator into a set."""
        from nu.ops.builtins.conversion import ToSetOp
        from ...values import SetValue

        return SetValue(ToSetOp(self))

    def to_tuple(self) -> TupleValue:
        """Materialize iterator into a tuple."""
        from nu.ops.builtins.conversion import ToTupleOp
        from ...values import TupleValue

        return TupleValue(ToTupleOp(self))
