"""Set operations for Term expressions.

This module provides type-safe operations on set Terms:

Set operations: UnionOp, IntersectionOp, DifferenceOp, SymmetricDifferenceOp
Set tests: IsSubsetOp, IsSupersetOp, IsDisjointOp

Design principles:
1. Atomic classes: one operation = one class
2. All arguments support Term or literal
3. Proper base class inheritance (BinaryOp)
4. Runtime type checking with INVALID for invalid types
"""

from __future__ import annotations

from everyterm.term import BinaryOp
from everyterm.typing import INVALID, Sentinel


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


class UnionOp[T](BinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set union: set.union(other) or set | other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.union(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.union(other)  # type: ignore
        return INVALID


class IntersectionOp[T](BinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set intersection: set.intersection(other) or set & other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.intersection(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.intersection(other)  # type: ignore
        return INVALID


class DifferenceOp[T](BinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set difference: set.difference(other) or set - other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
        if isinstance(operand, frozenset):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.difference(other)  # type: ignore
        if isinstance(operand, set):
            if not isinstance(other, (set, frozenset)):
                return INVALID
            return operand.difference(other)  # type: ignore
        return INVALID


class SymmetricDifferenceOp[T](BinaryOp[set[T] | frozenset[T] | Sentinel]):
    """Set symmetric difference: set.symmetric_difference(other) or set ^ other."""

    def _apply_op(self, operand: object, other: object) -> set[T] | frozenset[T] | Sentinel:
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


class IsSubsetOp(BinaryOp[bool | Sentinel]):
    """Test if subset: set.issubset(other) or set <= other."""

    def _apply_op(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return INVALID
        if not isinstance(other, (set, frozenset)):
            return INVALID
        return operand.issubset(other)


class IsSupersetOp(BinaryOp[bool | Sentinel]):
    """Test if superset: set.issuperset(other) or set >= other."""

    def _apply_op(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return INVALID
        if not isinstance(other, (set, frozenset)):
            return INVALID
        return operand.issuperset(other)


class IsDisjointOp(BinaryOp[bool | Sentinel]):
    """Test if disjoint: set.isdisjoint(other)."""

    def _apply_op(self, operand: object, other: object) -> bool | Sentinel:
        if not isinstance(operand, (set, frozenset)):
            return INVALID
        if not isinstance(other, (set, frozenset)):
            return INVALID
        return operand.isdisjoint(other)
