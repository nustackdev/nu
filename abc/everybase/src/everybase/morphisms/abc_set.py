"""Set morphisms for everybase.

Set operations: UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
Set tests: IsSubsetOp, IsSupersetOp, IsDisjointOp
"""

from __future__ import annotations

from collections.abc import Set

from everyabc import INVALID, BinaryOperation, Sentinel


__all__ = [
    "DifferenceOp",
    "IntersectionOp",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "SymmetricDifferenceOp",
    "UnionOp",
]


# =============================================================================
# SET OPERATIONS (Binary)
# =============================================================================


class UnionOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set union: left | right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left | right  # type: ignore


class IntersectionOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set intersection: left & right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left & right  # type: ignore


class DifferenceOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set difference: left - right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left - right  # type: ignore


class SymmetricDifferenceOp[T](BinaryOperation[set[T] | frozenset[T]]):
    """Set symmetric difference: left ^ right."""

    def apply(self, left: object, right: object) -> set[T] | frozenset[T] | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left ^ right  # type: ignore


# =============================================================================
# SET TESTS (Binary)
# =============================================================================


class IsSubsetOp(BinaryOperation[bool]):
    """Test if subset: left <= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left <= right


class IsSupersetOp(BinaryOperation[bool]):
    """Test if superset: left >= right."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left >= right


class IsDisjointOp(BinaryOperation[bool]):
    """Test if disjoint: left.isdisjoint(right)."""

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Set) or not isinstance(right, Set):
            return INVALID
        return left.isdisjoint(right)
