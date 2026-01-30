"""Set capability base — Collection + set operations.

Follows Python's collections.abc.Set pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .col_collection_base import CollectionBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef


__all__ = [
    "SetLikeBase",
]


class SetLikeBase[ElementT, ResultT](
    CollectionBase[ElementT, ResultT],
):
    """Base for set values — like collections.abc.Set."""

    def _wrap_set_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set union."""
        from everybase.morphisms.abc_set import UnionOp

        return cast("ResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set intersection."""
        from everybase.morphisms.abc_set import IntersectionOp

        return cast("ResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set difference."""
        from everybase.morphisms.abc_set import DifferenceOp

        return cast("ResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set symmetric difference."""
        from everybase.morphisms.abc_set import SymmetricDifferenceOp

        return cast("ResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef:
        """Check if subset."""
        from everybase.morphisms.abc_set import IsSubsetOp
        from everybase.py import BoolRef

        return BoolRef(IsSubsetOp(self, other))

    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef:
        """Check if superset."""
        from everybase.morphisms.abc_set import IsSupersetOp
        from everybase.py import BoolRef

        return BoolRef(IsSupersetOp(self, other))

    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef:
        """Check if disjoint."""
        from everybase.morphisms.abc_set import IsDisjointOp
        from everybase.py import BoolRef

        return BoolRef(IsDisjointOp(self, other))
