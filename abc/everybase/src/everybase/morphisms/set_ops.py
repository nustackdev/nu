"""Set morphisms for everybase.

Set operations: UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
Set tests: IsSubsetOp, IsSupersetOp, IsDisjointOp
"""

from __future__ import annotations

from everyabc import INVALID, BinaryMorphism, Operation, Sentinel


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


class UnionOp[T](Operation, BinaryMorphism[set[T] | frozenset[T] | Sentinel]):
    """Set union: set.union(other) or set | other."""

    def _apply(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.union(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.union(other)  # type: ignore
        return INVALID


class IntersectionOp[T](Operation, BinaryMorphism[set[T] | frozenset[T] | Sentinel]):
    """Set intersection: set.intersection(other) or set & other."""

    def _apply(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.intersection(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.intersection(other)  # type: ignore
        return INVALID


class DifferenceOp[T](Operation, BinaryMorphism[set[T] | frozenset[T] | Sentinel]):
    """Set difference: set.difference(other) or set - other."""

    def _apply(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.difference(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.difference(other)  # type: ignore
        return INVALID


class SymmetricDifferenceOp[T](Operation, BinaryMorphism[set[T] | frozenset[T] | Sentinel]):
    """Set symmetric difference: set.symmetric_difference(other) or set ^ other."""

    def _apply(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.symmetric_difference(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.symmetric_difference(other)  # type: ignore
        return INVALID


# =============================================================================
# SET TESTS (Binary)
# =============================================================================


class IsSubsetOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Test if subset: set.issubset(other) or set <= other."""

    def _apply(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return INVALID
        if not isinstance(other, (set, frozenset)):
            return INVALID
        return operand.issubset(other)


class IsSupersetOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Test if superset: set.issuperset(other) or set >= other."""

    def _apply(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return INVALID
        if not isinstance(other, (set, frozenset)):
            return INVALID
        return operand.issuperset(other)


class IsDisjointOp(Operation, BinaryMorphism[bool | Sentinel]):
    """Test if disjoint: set.isdisjoint(other)."""

    def _apply(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return INVALID
        if not isinstance(other, (set, frozenset)):
            return INVALID
        return operand.isdisjoint(other)
