# ruff: noqa: D102
"""Set capability protocol — Collection + set operations.

Follows Python's collections.abc.Set pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .col_collection_protocol import CollectionProtocol


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef


__all__ = [
    "SetLikeProtocol",
]


class SetLikeProtocol[ElementT, ResultT](
    CollectionProtocol[ElementT, ResultT],
    Protocol,
):
    """Protocol for set values — like collections.abc.Set."""

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT: ...
    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT: ...
    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT: ...
    def symmetric_difference(
        self, other: set[ElementT] | frozenset[ElementT] | Term
    ) -> ResultT: ...
    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef: ...
    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef: ...
    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef: ...
